"""Module to type-check the fields for a patient file"""

import csv
import json
import re
import os
import argparse
#import rfc3986

RESOURCES_FOLDER = "output/resource"
TYPES_FOLDER = "output/types"

# Define the expected types and regex patterns
FHIR_TYPES = {
     'unsignedInt' : {'type':'integer', 'regex':'[0]|([1-9][0-9]*)'},
     'boolean' : {'type':'boolean', 'regex':'true|false'},
     'uri' : {'type':'string', 'regex':'\S*'},
     'url' : {'type':'string', 'regex':'\S*'},
     'string' : {'type':'string', 'regex':'[ \r\n\t\S]+'},
     'base64Binary' : {'type':'string', 'regex':'(\s*([0-9a-zA-Z\+\=]){4}\s*)+'},
     'date' : {'type':'date', 'regex':'([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1]))?)?'},
     'uuid' : {'type':'string', 'regex':'urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'},
     'decimal' : {'type':'decimal', 'regex':'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?'},
     'dateTime' : {'type':'datetime', 'regex':'([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1])(T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00)))?)?)?'},
     'positiveInt' : {'type':'integer', 'regex':'\+?[1-9][0-9]*'},
     'time' : {'type':'time', 'regex':'([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?'},
     'code' : {'type':'string', 'regex':'[^\s]+(\s[^\s]+)*'},
     'oid' : {'type':'string', 'regex':'urn:oid:[0-2](\.(0|[1-9][0-9]*))+'},
     'instant' : {'type':'datetime', 'regex':'([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))'},
     'integer' : {'type':'integer', 'regex':'[0]|[-+]?[1-9][0-9]*'},
     'markdown' : {'type':'string', 'regex':'\s*(\S|\s)*'},
     'canonical' : {'type':'string', 'regex':'\S*'},
     'id' : {'type':'string', 'regex':'[A-Za-z0-9\-\.]{1,64}'}
    }


def validate_field(field_name, value, field_type, err_list):
    """ Validate field value against expected type and regex. """

    if field_type not in FHIR_TYPES:
        return None
    expected_info = FHIR_TYPES[field_type]
    expected_python_type = expected_info["type"]
    regex_pattern = expected_info.get("regex")

    if expected_python_type == "boolean":
        if not isinstance(value, bool):
            err_list.append(f"Type mismatch: Expected boolean, got {type(value).__name__}")
    
    elif expected_python_type == "integer":
        if not isinstance(value, int):
            err_list.append(f"Type mismatch: Expected integer, got {type(value).__name__}")
        else: 
            value_pr = str(value)
            if regex_pattern and not re.fullmatch(regex_pattern, value_pr, re.IGNORECASE):
                err_list.append(f"Regex mismatch: Value '{value}' does not match {regex_pattern}")
    
    elif expected_python_type == "decimal":
        if not isinstance(value, (int,float)):
            err_list.append(f"Type mismatch: Expected decimal, got {type(value).__name__}")
        else:
            value_pr = str(value)
            if regex_pattern and not re.fullmatch(regex_pattern, value_pr, re.IGNORECASE):
                err_list.append(f"Regex mismatch: Value '{value}' does not match {regex_pattern}")
    
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
            err_list.append(f"Type mismatch: Expected string type, got {type(value).__name__}")
        else:
            if regex_pattern and not re.fullmatch(regex_pattern, value, re.IGNORECASE):
                    err_list.append(f"Regex mismatch: Value '{value}' does not match {regex_pattern}")


def parse_fhir_spec_csv(file_path):
    """Parse CSV file to extract all fields and their types and store as metadata."""
    metadata_fundamental = {}
    metadata_recursive = {}

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                field, field_type = row
                if field_type[0].islower():
                    metadata_fundamental[field] = {"type": field_type}
                elif field_type[0].isupper() and field_type.isalnum():
                    metadata_recursive[field] = {"type": field_type}

    return metadata_fundamental, metadata_recursive


def validate_nested_field(nested_field, value, metadata, recursive_metadata, error_list):
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
            validate_nested_field(nested_field, value, metadata, recursive_metadata, error_list)

    elif isinstance(patient_data, list):
        for item in patient_data:
            if isinstance(item, dict):
                for nested_field, value in item.items():
                    validate_nested_field(nested_field, value, metadata, recursive_metadata, error_list)


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
                    validate_nested_field(nested_field, value, metadata, recursive_metadata, err_list)


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
                validate_nested_field(nested_field, value, metadata, recursive_metadata, err_list)
    return err_list


def validate_multiple_patients(directory_path):
    """Validate all patient JSON files in a directory and output a list of errors."""
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            print(f"Processing {filename}")
            err_list = validate_patient_json(os.path.join(directory_path, filename))
            print(err_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate FHIR patient files.")
    parser.add_argument("path", help="Path to a patient JSON file or a directory containing multiple JSON files.")
    args = parser.parse_args()

    if os.path.isdir(args.path):
        print(f"Validating multiple patient files in directory: {args.path}")
        validate_multiple_patients(args.path)
    elif os.path.isfile(args.path) and args.path.endswith(".json"):
        print(f"Validating single patient file: {args.path}")
        err_list = validate_patient_json(args.path)
        print(err_list)
    else:
        print("Error: Invalid path. Please provide a valid JSON file or a directory containing JSON files.")