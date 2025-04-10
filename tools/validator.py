"""Module to type-check the fields for a patient file"""

import json
import re
import os
import argparse

# import rfc3986

from utils.fhir_utils import (
    parse_fhir_spec_csv,
    RESOURCES_FOLDER,
    TYPES_FOLDER,
    FHIR_TYPES,
)


def validate_field(field_name, value, field_type, err_list):
    """Validate field value against expected type and regex."""

    if field_type not in FHIR_TYPES:
        return None
    expected_info = FHIR_TYPES[field_type]
    expected_python_type = expected_info["type"]
    regex_pattern = expected_info.get("regex")

    if expected_python_type == "boolean":
        if not isinstance(value, bool):
            err_list.append(
                f"Type mismatch: Expected boolean, got {type(value).__name__}"
            )

    elif expected_python_type == "integer":
        if not isinstance(value, int):
            err_list.append(
                f"Type mismatch: Expected integer, got {type(value).__name__}"
            )
        else:
            value_pr = str(value)
            if regex_pattern and not re.fullmatch(
                regex_pattern, value_pr, re.IGNORECASE
            ):
                err_list.append(
                    f"Regex mismatch: Value '{value}' does not match {regex_pattern}"
                )

    elif expected_python_type == "decimal":
        if not isinstance(value, (int, float)):
            err_list.append(
                f"Type mismatch: Expected decimal, got {type(value).__name__}"
            )
        else:
            value_pr = str(value)
            if regex_pattern and not re.fullmatch(
                regex_pattern, value_pr, re.IGNORECASE
            ):
                err_list.append(
                    f"Regex mismatch: Value '{value}' does not match {regex_pattern}"
                )

    else:
        # Includes string, date, datetime with type as string

        # # Commenting the check for uri, url, canonical forms. Some url fields have plaintext not of url format consistently across
        # # all patient files.
        # uri_checklist = ['uri', 'url', 'canonical']
        # valid_schemes = {"http", "https", "ftp", "mailto", "mllp"}

        # if field_name in uri_checklist:
        #     parsed = rfc3986.uri_reference(value)
        #     if field_name != 'url' and not parsed.is_valid():
        #         err_list.append(f"Value mismatch: Value '{value}' not valid URI.")
        #     if field_name == 'url':
        #         if not (parsed.is_valid() and parsed.scheme in valid_schemes):
        #             err_list.append(f"Value mismatch: Value '{value}' not valid URL.")

        if not isinstance(value, str):
            err_list.append(
                f"Type mismatch: Expected string type, got {type(value).__name__}"
            )
        else:
            if regex_pattern and not re.fullmatch(regex_pattern, value, re.IGNORECASE):
                err_list.append(
                    f"Regex mismatch: Value '{value}' does not match {regex_pattern}"
                )


def validate_nested_field(
    nested_field, value, metadata, recursive_metadata, error_list
):
    """Validate a nested field and handle recursion if needed."""
    if nested_field in metadata:
        field_type = metadata[nested_field]["type"]
        if isinstance(value, list):
            for item in value:
                validate_field(nested_field, item, field_type, error_list)
        else:
            validate_field(nested_field, value, field_type, error_list)

    if nested_field in recursive_metadata:
        recursive_traversal(value, recursive_metadata[nested_field]["type"], error_list)


def recursive_traversal(patient_data, field_type, error_list):
    """Recursively traverse nested patient data up to 12 levels deep."""
    if field_type == "Resource":
        double_resource_call(patient_data, error_list)
        return

    resourcetype_csv = os.path.join(TYPES_FOLDER, f"{field_type}.csv")
    metadata, recursive_metadata = parse_fhir_spec_csv(resourcetype_csv)

    if isinstance(patient_data, dict):
        for nested_field, value in patient_data.items():
            validate_nested_field(
                nested_field, value, metadata, recursive_metadata, error_list
            )

    elif isinstance(patient_data, list):
        for item in patient_data:
            if isinstance(item, dict):
                for nested_field, value in item.items():
                    validate_nested_field(
                        nested_field, value, metadata, recursive_metadata, error_list
                    )


def double_resource_call(patient_data, err_list):
    """Process resources within another resource in a patient data."""
    if isinstance(patient_data, list):
        for res in patient_data:
            resource_type = res.get("resourceType")
            if not resource_type:
                continue

            resourcetype_csv = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
            metadata, recursive_metadata = parse_fhir_spec_csv(resourcetype_csv)

            for nested_field, value in res.items():
                if nested_field != "resourceType":
                    validate_nested_field(
                        nested_field, value, metadata, recursive_metadata, err_list
                    )


def validate_patient_json(file_path):
    """Validate a single patient JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        patient_data = json.load(f)

    err_list = []

    if not patient_data:
        return

    for entry in patient_data.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if not resource_type:
            continue

        resourcetype_csv = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
        metadata, recursive_metadata = parse_fhir_spec_csv(resourcetype_csv)

        for nested_field, value in resource.items():
            if nested_field != "resourceType":
                validate_nested_field(
                    nested_field, value, metadata, recursive_metadata, err_list
                )
    return err_list


def validate_multiple_patients(directory_path):
    """Validate all patient JSON files in a directory and output a list of errors."""
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            print(f"Processing {filename}")
            _ = validate_patient_json(os.path.join(directory_path, filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate FHIR patient files.")
    parser.add_argument(
        "path",
        help="Path to a patient JSON file or a directory containing multiple JSON files.",
    )
    args = parser.parse_args()

    if os.path.isdir(args.path):
        print(f"Validating multiple patient files in directory: {args.path}")
        validate_multiple_patients(args.path)
    elif os.path.isfile(args.path) and args.path.endswith(".json"):
        print(f"Validating single patient file: {args.path}")
        err_list = validate_patient_json(args.path)
        print(err_list)
    else:
        print(
            "Error: Invalid path. Please provide a valid JSON file or a directory containing JSON files."
        )
