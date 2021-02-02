import json
import pathlib
import os
import warnings

import PIL.Image
import yaml
import imagehash


def get_image_dimensions(path):
    """
    Function to measure image dimensions and calculate resolution.
    """
    if not os.path.isfile(path):
        warnings.warn(f"Could not open {path}")
        return None
    # Retrieve image width and height
    image = PIL.Image.open(path)
    width, height = image.size
    return {"width": width, "height": height}


def load_json_or_yaml(path):
    """Streamlined function for open both JSON and YAML"""
    with open(path) as f:
        if path.suffix in (".yml", ".yaml"):
            obj = yaml.safe_load(f)
        else:
            obj = json.load(f)
    return obj


def add_agcontext_from_file(coco, agcontext_path):
    """Make all images have the same AgContext loaded from YAML or JSON"""
    agcontext = load_json_or_yaml(agcontext_path)
    if "id" not in agcontext:
        agcontext["id"] = 0
    coco["agcontexts"] = [agcontext]
    for image in coco["images"]:
        image["agcontext_id"] = agcontext["id"]
    return coco


def add_collection_from_file(coco, collection_path):
    """Make all annotations members of one collection loaded from YAML or JSON"""
    collection = load_json_or_yaml(collection_path)
    if "id" not in collection:
        collection["id"] = 0
    coco["collections"] = [collection]
    coco["collection_memberships"] = [
        {"annotation_id": annotation["id"], "collection_id": collection["id"]}
        for annotation in coco["annotations"]
    ]
    return coco


def get_image_average_hash(path, hash_size=8):
    """Return an average hash of an image"""
    return str(imagehash.average_hash(PIL.Image.open(path), hash_size=hash_size))


def check_if_approved_image_extension(image_name):
    return image_name.lower().endswith((".png", ".jpg", ".jpeg", ".tiff"))


def check_if_approved_image_format(image_ext):
    return image_ext in ("PNG", "JPG", "JPEG", "TIFF")


def _get_growth_stage_names():
    global __GROWTH_STAGE_NAMES
    try:
        return __GROWTH_STAGE_NAMES
    except NameError:
        pass
    data_path = pathlib.Path(__file__).parent / "growth_stage_labels.json"
    data = json.load(open(data_path))
    out = {}
    # JSON requires string keys
    out["fine"] = {int(k): v for k, v in data.pop("fine").items()}
    for scheme, ranges in data.items():
        out[scheme] = {}
        for range_ in ranges:
            for i in range(range_["lo"], range_["hi"] + 1):
                out[scheme][i] = range_["label"]
    __GROWTH_STAGE_NAMES = out
    return out


def lookup_growth_stage_name(idx, scheme):
    valid = ["fine", "bbch_ranges", "grain_ranges"]
    if scheme not in valid:
        raise ValueError(f"scheme must be one of {valid}. Got {scheme}")
    return _get_growth_stage_names()[scheme][idx]
