"""Validation tools for WeedCOCO
"""
import pathlib
import argparse
import sys
import json

from jsonschema.validators import Draft7Validator, RefResolver
import yaml

SCHEMA_DIR = pathlib.Path(__file__).parent / "schema"
MAIN_SCHEMAS = {
    "weedcoco": "https://weedid.sydney.edu.au/schema/main.json",
    "compatible-coco": "https://weedid.sydney.edu.au/schema/compatible-coco.json",
}


class ValidationError(Exception):
    pass


class JsonValidationError(ValidationError):
    def __init__(self, message, jsonschema_errors=None):
        super().__init__(message)
        self.jsonschema_errors = jsonschema_errors

    def get_error_details(self):
        error_details = [
            {
                "path": list(error.path),
                "value": error.instance,
                "message": error.message,
                "schema": error.schema,
            }
            for error in self.jsonschema_errors
        ]
        return {
            "error_type": "jsonschema",
            "n_errors_found": str(len(error_details)),
            "error_details": error_details,
        }


def validate_json(weedcoco, schema="weedcoco", schema_dir=SCHEMA_DIR):
    """Check that the weedcoco matches its JSON schema"""
    if schema not in MAIN_SCHEMAS:
        raise ValueError(f"schema should be one of {sorted(MAIN_SCHEMAS)}")
    try:
        # memoise the schema
        ref_store = validate_json.ref_store
    except AttributeError:
        schema_objects = [
            yaml.safe_load(path.open()) for path in schema_dir.glob("*.yaml")
        ]
        validate_json.ref_store = {obj["$id"]: obj for obj in schema_objects}
        ref_store = validate_json.ref_store
    schema_uri = MAIN_SCHEMAS[schema]
    main_schema = ref_store[schema_uri]
    validator = Draft7Validator(main_schema)
    validator.resolver = RefResolver(schema_uri, main_schema, store=ref_store)
    errors = [error for error in validator.iter_errors(weedcoco)]
    if len(errors):
        raise JsonValidationError(
            f"{len(errors)} violations found: {' '.join(err.message for err in errors)}",
            errors,
        )


def validate_references(
    weedcoco,
    schema_dir=SCHEMA_DIR,
    require_reference=("image", "agcontext"),
):
    """Check that all IDs are unique and references valid"""
    known_ids = set()
    referenced_ids = set()

    # ensure IDs are unique per section
    for section_name, section in weedcoco.items():
        if section_name.endswith("s"):
            section_name_singular = section_name[:-1]
            if section_name.endswith("ies"):
                section_name_singular = section_name[:-3] + "y"
        else:
            section_name_singular = section_name
        if isinstance(section, list):
            for obj in section:
                id_key = (section_name_singular, obj["id"])
                if id_key in known_ids:
                    raise ValidationError(f"Duplicate ID: {id_key}")
                else:
                    known_ids.add(id_key)

    # ensure referenced IDs are known
    # FIXME: this should be more precise, checking the relationship between
    # the referring and referent sections.
    for section_name, section in weedcoco.items():
        if isinstance(section, list):
            for obj in section:
                for key, val in obj.items():
                    if key.endswith("_id"):
                        id_key = (key[:-3], val)
                        if id_key not in known_ids:
                            raise ValidationError(
                                f"Reference to unknown ID: {id_key}. "
                                f"Found in {section_name} id {obj.get('id')}"
                            )
                        referenced_ids.add(id_key)

    for known_id in known_ids:
        section_name = known_id[0]
        if section_name in require_reference and known_id not in referenced_ids:
            raise ValidationError(f"{section_name} ID {known_id[1]} is unreferenced")
    # TODO: consider warning if not require_reference


def validate_coordinates(weedcoco):
    """Check that annotation coordinates are within the image"""
    # TODO


def validate_image_sizes(weedcoco, images_root):
    """Check that all image sizes match the image files"""
    # TODO


def validate(weedcoco, images_root=None, schema="weedcoco"):
    if hasattr(weedcoco, "read"):
        weedcoco = json.load(weedcoco)
    validate_json(weedcoco, schema=schema)
    validate_references(weedcoco)
    validate_coordinates(weedcoco)
    if images_root is not None:
        validate_image_sizes(weedcoco, images_root)


def main():
    ap = argparse.ArgumentParser("WeedCOCO Validator")
    ap.add_argument("paths", nargs="+", type=argparse.FileType("r"))
    ap.add_argument("--schema", default="weedcoco", choices=MAIN_SCHEMAS.keys())
    ap.add_argument(
        "--images-root", default=".", help="Root for image file names. Default=."
    )
    ap.add_argument(
        "--disable-size-check",
        action="store_const",
        dest="images_root",
        const=None,
        help="Disable validating image sizes are correct, which requires paths to be valid",
    )
    args = ap.parse_args()
    for path in args.paths:
        try:
            validate(path, images_root=args.images_root, schema=args.schema)
        except Exception:
            print(f"While validating {path}", file=sys.stderr)
            raise


if __name__ == "__main__":
    main()
