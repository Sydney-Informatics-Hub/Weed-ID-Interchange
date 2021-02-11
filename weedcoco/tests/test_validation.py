"""Tests for weedcoco.validation"""

import functools
import copy
import random

import pytest

from weedcoco.validation import (
    validate,
    validate_json,
    validate_references,
    validate_coordinates,
    validate_image_sizes,
    ValidationError,
)

validate_image_sizes_null = functools.partial(validate_image_sizes, images_root=None)
validate_image_sizes_cwd = functools.partial(validate_image_sizes, images_root=".")


MINIMAL_WEEDCOCO = {
    "images": [],
    "annotations": [],
    "categories": [],
    "agcontexts": [],
    "info": {
        "description": "Something",
        "metadata": {
            "name": "Something",
            "creator": [{"name": "Someone"}],
            "datePublished": "XXXX-XX-XX",
            "license": "https://creativecommons.org/licenses/by/4.0/",
        },
    },
}

SMALL_WEEDCOCO = {
    "images": [
        {
            "id": 46,
            "file_name": "cwfid_images/046_image.png",
            "license": 0,
            "agcontext_id": 0,
            "width": 1296,
            "height": 966,
        },
        {
            "id": 1,
            "file_name": "cwfid_images/001_image.png",
            "license": 0,
            "agcontext_id": 0,
            "width": 1296,
            "height": 966,
        },
    ],
    "annotations": [
        {
            "id": 0,
            "image_id": 46,
            "category_id": 0,
            "segmentation": [[596, 207, 521]],
            "iscrowd": 0,
        },
        {
            "id": 1,
            "image_id": 46,
            "category_id": 0,
            "segmentation": [[689, 787, 589, 745]],
            "iscrowd": 0,
        },
        {
            "id": 2,
            "image_id": 46,
            "category_id": 1,
            "segmentation": [[486, 335, 399]],
            "iscrowd": 0,
        },
        {
            "id": 3,
            "image_id": 1,
            "category_id": 1,
            "segmentation": [[810, 225, 841, 234]],
            "iscrowd": 0,
        },
        {
            "id": 4,
            "image_id": 1,
            "category_id": 1,
            "segmentation": [[1070, 626, 1055, 722]],
            "iscrowd": 0,
        },
    ],
    "categories": [
        {
            "name": "crop: daugus carota",
            "common_name": "carrot",
            "species": "daugus carota",
            "eppo_taxon_code": "DAUCS",
            "eppo_nontaxon_code": "3UMRC",
            "role": "crop",
            "id": 0,
        },
        {
            "name": "weed: unspecified",
            "species": "UNSPECIFIED",
            "role": "weed",
            "id": 1,
        },
    ],
    "info": {
        "description": "Cwfid annotations converted into WeedCOCO",
        "metadata": {
            "name": "Cwfid annotations converted into WeedCOCO",
            "creator": [{"name": "Sebastian Haug"}],
            "datePublished": "2015-XX-XX",
            "license": "https://github.com/cwfid/dataset",
        },
    },
    "license": [
        {
            "id": 0,
            "url": "https://github.com/cwfid/dataset",
        }
    ],
    "agcontexts": [
        {
            "id": 0,
            "agcontext_name": "cwfid",
            "crop_type": "other",
            "bbch_growth_range": [10, 20],
            "soil_colour": "grey",
            "surface_cover": "none",
            "surface_coverage": "0-25",
            "weather_description": "sunny",
            "location_lat": 53,
            "location_long": 11,
            "location_datum": 4326,
            "camera_make": "JAI AD-130GE",
            "camera_lens": "Fujinon TF15-DA-8",
            "camera_lens_focallength": 15,
            "camera_height": 450,
            "camera_angle": 90,
            "camera_fov": 22.6,
            "photography_description": "Mounted on boom",
            "lighting": "natural",
            "cropped_to_plant": False,
        }
    ],
}


def _set_category_name(coco, name):
    coco = copy.deepcopy(coco)
    print(coco)
    coco["categories"][0]["name"] = name
    return coco


@pytest.mark.parametrize("func", [validate, validate_json])
@pytest.mark.parametrize(
    "bad_weedcoco",
    [
        {},
        {"images": [], "annotations": []},
        {"images": [], "annotations": [], "categories": []},
    ],
)
def test_missing_required_at_root(func, bad_weedcoco):
    with pytest.raises(ValidationError, match="is a required property"):
        func(bad_weedcoco)


@pytest.mark.parametrize(
    "func",
    [
        validate,
        validate_json,
        validate_references,
        validate_coordinates,
        validate_image_sizes_null,
        validate_image_sizes_cwd,
    ],
)
def test_okay(func):
    func(MINIMAL_WEEDCOCO)
    func(SMALL_WEEDCOCO)


@pytest.mark.parametrize("func", [validate, validate_json])
@pytest.mark.parametrize("bad_name", ["foobar", "weed 1"])
def test_bad_category_name(func, bad_name):
    weedcoco = copy.deepcopy(SMALL_WEEDCOCO)
    weedcoco = _set_category_name(weedcoco, bad_name)
    with pytest.raises(ValidationError):
        func(weedcoco)


def _make_duplicate_id(weedcoco, key, idx, insert_at=-1):
    weedcoco = copy.deepcopy(weedcoco)
    weedcoco[key].insert(insert_at, weedcoco[key][idx])
    return weedcoco


@pytest.mark.parametrize("func", [validate, validate_json])
@pytest.mark.parametrize(
    "removed_section",
    [
        "images",
        "annotations",
        "categories",
        "agcontexts",
    ],
)
def test_missing_section(func, removed_section):
    bad_weedcoco = copy.deepcopy(SMALL_WEEDCOCO)
    del bad_weedcoco[removed_section]
    with pytest.raises(ValidationError):
        func(bad_weedcoco)


@pytest.mark.parametrize("func", [validate, validate_references])
@pytest.mark.parametrize(
    "bad_weedcoco",
    [
        _make_duplicate_id(SMALL_WEEDCOCO, "images", idx=0),
        _make_duplicate_id(SMALL_WEEDCOCO, "images", idx=0, insert_at=0),
        _make_duplicate_id(SMALL_WEEDCOCO, "annotations", idx=2, insert_at=4),
    ],
)  # TODO
def test_duplicate_id(func, bad_weedcoco):
    with pytest.raises(ValidationError, match="Duplicate ID"):
        func(bad_weedcoco)


def _make_unknown_id(weedcoco, section, ref_key, new_id=1000):
    bad_weedcoco = copy.deepcopy(weedcoco)
    random.choice(bad_weedcoco[section])[ref_key] = new_id
    return bad_weedcoco


@pytest.mark.parametrize("func", [validate, validate_references])
@pytest.mark.parametrize(
    "bad_weedcoco",
    [
        _make_unknown_id(SMALL_WEEDCOCO, "annotations", "image_id"),
        _make_unknown_id(SMALL_WEEDCOCO, "annotations", "category_id"),
    ],
)  # TODO
def test_nonexistent_referent(func, bad_weedcoco):
    with pytest.raises(ValidationError, match="Reference to unknown ID"):
        func(bad_weedcoco)


def _make_unreferenced(weedcoco, section, new_id=1000):
    bad_weedcoco = copy.deepcopy(weedcoco)
    copied = copy.deepcopy(random.choice(bad_weedcoco[section]))
    copied["id"] = new_id
    bad_weedcoco[section].insert(random.randint(0, len(bad_weedcoco[section])), copied)
    return bad_weedcoco


@pytest.mark.parametrize("func", [validate, validate_references])
@pytest.mark.parametrize(
    "bad_weedcoco",
    [
        _make_unreferenced(SMALL_WEEDCOCO, "images"),
    ],
)  # TODO
def test_id_not_referenced(func, bad_weedcoco):
    with pytest.raises(ValidationError, match="is unreferenced"):
        func(bad_weedcoco)


def _weedcoco_to_coco(weedcoco):
    coco = copy.deepcopy(weedcoco)
    del coco["agcontexts"]
    del coco["collections"]
    del coco["collection_memberships"]
    # del coco["info"]["metadata"]
    for image in coco["images"]:
        del image["agcontext_id"]
    return coco


@pytest.mark.parametrize("func", [validate, validate_json])
@pytest.mark.parametrize(
    "coco",
    [
        _weedcoco_to_coco(MINIMAL_WEEDCOCO),
        _weedcoco_to_coco(SMALL_WEEDCOCO),
    ],
)
def test_coco_compatible_good(func, coco):
    func(coco, schema="compatible-coco")


@pytest.mark.parametrize("func", [validate, validate_json])
@pytest.mark.parametrize(
    "bad_coco",
    [
        # drop categories:
        {
            k: v
            for k, v in _weedcoco_to_coco(MINIMAL_WEEDCOCO).items()
            if k != "categories"
        },
        # drop annotations:
        {
            k: v
            for k, v in _weedcoco_to_coco(MINIMAL_WEEDCOCO).items()
            if k != "annotations"
        },
        # rename to WeedCOCO-incompatible categories:
        _set_category_name(_weedcoco_to_coco(SMALL_WEEDCOCO), "foobar"),
    ],
)
def test_coco_compatible_bad(func, bad_coco):
    with pytest.raises(ValidationError):
        func(bad_coco, schema="compatible-coco")
