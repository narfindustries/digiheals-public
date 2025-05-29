"""Module to mutate each field for a given patient data"""

import argparse
import os
import json
import copy
import time
import base64
import random
import string
from datetime import datetime, timezone, timedelta
import exrex

from utils.fhir_utils import parse_fhir_spec_csv, RESOURCES_FOLDER, TYPES_FOLDER

# xhtml type has been ignored, as there is no regex defined for it
"""
1. base64Binary : regex generate by exrex throws parsing error.
2. time : regex generates microseconds, which is rejected by some servers. Also, it allows for 60 seconds to exist, which is an invalid time.
3. code: regex is too broad, and generates very random text.
4. datetime: regex generates only year which is required. The month, day, time, and timezone are all optional. Some servers reject this, when the 
             complete datetime is missing.
5. markdown: regex too permissive, using hardcoded string instead.
6. instant: regex generates seconds with 60, which is invalid. Also, it allows for n digits of microseconds, which few servers reject. New regex
            only allows for 6 digits of microseconds.
"""
FHIR_TYPES = {
    "unsignedInt": {"type": "integer", "regex": "[0]|([1-9][0-9]*)"},
    "boolean": {"type": "boolean", "regex": "true|false"},
    "uri": {"type": "string", "regex": "\S*"},
    "url": {"type": "string", "regex": "\S*"},
    "string": {"type": "string", "regex": "[a-zA-Z0-9]+"},
    "base64Binary": {
        "type": "string",
        "generator": lambda: base64.b64encode(os.urandom(16)).decode("utf-8"),
        "regex": "(\s*([0-9a-zA-Z\+\=]){4}\s*)+",
    },
    "date": {
        "type": "date",
        "regex": "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1]))?)?",
    },
    "uuid": {
        "type": "string",
        "regex": "urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    },
    "decimal": {
        "type": "decimal",
        "regex": "-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?",
    },
    "positiveInt": {"type": "integer", "regex": "\+?[1-9][0-9]*"},
    "instant": {
        "type": "datetime",
        "regex": "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])"
        "T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
        "(\.[0-9]{1,6})?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))",
    },
    "time": {
        "type": "time",
        "generator": lambda: f"{random.randint(0, 23):02}:{random.randint(0, 59):02}:{random.randint(0, 59):02}",
    },
    "code": {
        "type": "code",
        "generator": lambda: "".join(random.choices(string.ascii_letters, k=2)).upper(),
    },
    "oid": {"type": "string", "regex": "urn:oid:[0-2](\.(0|[1-9][0-9]*))+"},
    "dateTime": {
        "type": "datetime",
        "generator": lambda: (
            datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10000))
        ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        + random.choice(["Z", "-04:00", "+02:00"]),
    },
    "integer": {"type": "integer", "regex": "[0]|[-+]?[1-9][0-9]*"},
    "markdown": {
        "type": "string",
        "generator": lambda: "This is **markdown** text with _formatting_.",
    },
    "canonical": {"type": "string", "regex": "\S*"},
    "id": {"type": "string", "regex": "[A-Za-z0-9\-\.]{1,64}"},
    "largeString": {"type": "largestring", "value": "A" * 1024},
    "largeInt": {"type": "largeinteger", "value": 2**200},
    "largeFloat": {"type": "largefloat", "value": 1.7976931348623157e308},
}


def generate_value_from_type_info(regex_info):
    """Generate a value based on the provided regex information."""
    if "generator" in regex_info:
        return regex_info["generator"]()
    if "value" in regex_info:
        return regex_info["value"]

    regex = regex_info["regex"]
    val = exrex.getone(regex)

    # Fixed values for specific types
    if regex_info["type"] == "integer":
        return 456
    elif regex_info["type"] == "decimal":
        return 123.45
    elif regex_info["type"] == "boolean":
        return bool(val)
    if regex_info["type"] == "date":
        return "9000-11-30"
    if val == "":
        return "placeholder"
    return val


def fill_missing_basic_fields(resource_dict, resource_type):
    """Fill fields that are basic types"""
    csv_path = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
    if not os.path.exists(csv_path):
        print(f"Metadata CSV not found for {resource_type}")
        return resource_dict

    metadata, _ = parse_fhir_spec_csv(csv_path)

    for field, type_info in metadata.items():
        min_val = type_info["min"]
        max_val = type_info["max"]
        if field not in resource_dict:
            field_type = type_info["type"]
            if field_type in FHIR_TYPES:
                regex_info = FHIR_TYPES[field_type]
                if field_type == "code":
                    if type_info["codes"] == [""]:
                        generated_value = "SAMP"
                    else:
                        int_num = random.randint(0, len(type_info["codes"]) - 1)
                        generated_value = type_info["codes"][int_num]
                else:
                    generated_value = generate_value_from_type_info(regex_info)
                if field_type in ["uri", "url", "canonical"]:
                    generated_value = "http://hl7.org/fhir/StructureDefinition/example"
                if max_val == "Infinity":
                    resource_dict[field] = [generated_value]
                else:
                    resource_dict[field] = generated_value
                print(
                    f"Added missing field '{field}' to {resource_type} with value: {generated_value}"
                )

    return resource_dict


def fill_missing_nested_fields(resource_dict, resource_type):
    """Fill fields that are nested types"""
    csv_path = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join(TYPES_FOLDER, f"{resource_type}.csv")
        if not os.path.exists(csv_path):
            print(f"Metadata CSV not found for {resource_type}")
            return resource_dict

    _, recursive_metadata = parse_fhir_spec_csv(csv_path)

    for field, type_info in recursive_metadata.items():
        if (
            field == "contained" and type_info["type"] == "Resource"
        ) or field == "modifierExtension":
            # Skip contained type as it further nests into another resource. Skip modifierExtension as document says they are better avoided
            continue

        min_val = type_info["min"]
        max_val = type_info["max"]

        nested_type = type_info["type"]
        nested_csv_path = os.path.join(RESOURCES_FOLDER, f"{nested_type}.csv")
        if not os.path.exists(nested_csv_path):
            nested_csv_path = os.path.join(TYPES_FOLDER, f"{nested_type}.csv")
        if not os.path.exists(nested_csv_path):
            print(f"Metadata CSV not found for {nested_type}")
            continue

        if field not in resource_dict:
            resource_dict[field] = (
                [{}]
                if field == "modifierExtension"
                or field == "extension"
                or max_val == "Infinity"
                else {}
            )
            if nested_type == "CodeableConcept":
                system = type_info["system_url"]
                code = random.choice(type_info["codes"])
                resource_dict[field] = {"coding": [{"system": system, "code": code}]}
                if max_val == "Infinity":
                    resource_dict[field] = [resource_dict[field]]

            if nested_type == "Reference":
                id_val = generate_value_from_type_info(FHIR_TYPES["string"])
                reference_val = f"{type_info['references'][0]}/123"
                ref_type = f"{type_info['references'][0]}"
                display_val = generate_value_from_type_info(FHIR_TYPES["string"])
                resource_dict[field] = {
                    "id": id_val,
                    "reference": reference_val,
                    "type": ref_type,
                    "display": display_val,
                }
                if max_val == "Infinity":
                    resource_dict[field] = [resource_dict[field]]

            if nested_type == "Narrative" and field == "text":
                id_val = generate_value_from_type_info(FHIR_TYPES["string"])
                status = "generated"
                div = "<div xmlns='http://www.w3.org/1999/xhtml'>Sample Narrative</div>"
                resource_dict[field] = {"id": id_val, "status": status, "div": div}

        meta_fund, _ = parse_fhir_spec_csv(nested_csv_path)

        if isinstance(resource_dict[field], dict):

            if nested_type == "Reference":
                id_val = generate_value_from_type_info(FHIR_TYPES["string"])
                reference_val = f"{type_info['references'][0]}/123"
                ref_type = f"{type_info['references'][0]}"
                display_val = generate_value_from_type_info(FHIR_TYPES["string"])
                resource_dict[field] = {
                    "id": id_val,
                    "reference": reference_val,
                    "type": ref_type,
                    "display": display_val,
                }
                if max_val == "Infinity":
                    resource_dict[field] = [resource_dict[field]]

            for subfield, sub_type_info in meta_fund.items():

                sub_type = sub_type_info["type"]

                if subfield not in resource_dict[field] and sub_type in FHIR_TYPES:

                    if sub_type == "code":
                        if sub_type_info["codes"] == [""]:
                            val = "SAMP"
                        else:
                            int_num = random.randint(0, len(sub_type_info["codes"]) - 1)
                            val = sub_type_info["codes"][int_num]
                    else:
                        val = generate_value_from_type_info(FHIR_TYPES[sub_type])

                    if subfield == "suffix" or subfield == "profile":
                        val = [val]

                    if max_val == "Infinity":
                        resource_dict[field][0][subfield] = val
                    else:
                        resource_dict[field][subfield] = val

        elif isinstance(resource_dict[field], list):
            for _, item in enumerate(resource_dict[field]):
                if isinstance(item, dict):
                    if nested_type == "Reference":
                        id_val = generate_value_from_type_info(FHIR_TYPES["string"])
                        reference_val = f"{type_info['references'][0]}/123"
                        ref_type = f"{type_info['references'][0]}"
                        display_val = generate_value_from_type_info(
                            FHIR_TYPES["string"]
                        )
                        resource_dict[field] = {
                            "id": id_val,
                            "reference": reference_val,
                            "type": ref_type,
                            "display": display_val,
                        }
                        if max_val == "Infinity":
                            resource_dict[field] = [resource_dict[field]]

                    if field == "extension":
                        if "extension" in item or resource_dict[field][0] != {}:
                            # Handle special case for Extension
                            continue

                        else:
                            ext_list = []
                            url = "http://synthetichealth.github.io/synthea/disability-adjusted-life-years"
                            for subfield, sub_type_info in meta_fund.items():
                                temp_json = {}
                                if subfield not in ["url", "id", "extension"]:
                                    temp_json["url"] = url
                                    temp_json[subfield] = generate_value_from_type_info(
                                        FHIR_TYPES[sub_type_info["type"]]
                                    )
                                    ext_list.append(temp_json)
                            if field == "extension":
                                resource_dict[field] = []
                            resource_dict[field].extend(ext_list)
                            break
                    else:
                        for subfield, sub_type_info in meta_fund.items():
                            sub_type = sub_type_info["type"]
                            if subfield not in item and sub_type in FHIR_TYPES:
                                if sub_type == "code":
                                    if sub_type_info["codes"] == [""]:
                                        val = "SAMP"
                                    else:
                                        int_num = random.randint(
                                            0, len(sub_type_info["codes"]) - 1
                                        )
                                        val = sub_type_info["codes"][int_num]
                                else:
                                    val = generate_value_from_type_info(
                                        FHIR_TYPES[sub_type]
                                    )
                                if subfield == "suffix":
                                    val = [val]
                                item[subfield] = [val] if subfield == "profile" else val

        print(
            f"Filled nested field '{field}' in {resource_type} with type {nested_type}"
        )

    return resource_dict


def fill_all_missing_fields(resource_dict, resource_type):
    """Fill all missing fields in the resource dictionary."""
    resource_dict = fill_missing_basic_fields(resource_dict, resource_type)
    resource_dict = fill_missing_nested_fields(resource_dict, resource_type)
    return resource_dict


def fill_missing_fields_in_patient_file(patient_json):
    """Fill missing fields in the patient JSON file."""
    filled_patient = copy.deepcopy(patient_json)

    for entry in filled_patient.get("entry", []):
        resource = entry.get("resource")
        if not resource:
            continue
        resource_type = resource.get("resourceType")
        if not resource_type:
            continue
        if resource_type == "Patient":
            continue
        print(f"Processing resourceType: {resource_type}")
        resource = fill_all_missing_fields(resource, resource_type)
        entry["resource"] = resource

    return filled_patient


def modify_multiple_files(directory_path):
    """Validate all patient JSON files in a directory and output a list of errors."""
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            print(f"Processing {filename}")
            start_time = time.time()
            modify_single_file(os.path.join(directory_path, filename))
            end_time = time.time()

            elapsed_time = (end_time - start_time) / 60
            print(f"Time elapsed: {elapsed_time} min")


def modify_single_file(file_path):
    """
    Modify a single patient JSON file and return the filled JSON.
    """
    if not os.path.isfile(file_path) or not file_path.endswith(".json"):
        print(f"Error: {file_path} is not a valid JSON file.")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        patient_json = json.load(f)
        print(f"Loaded patient JSON from: {file_path}")

    filled_json = fill_missing_fields_in_patient_file(patient_json)

    filled_path = file_path.replace(".json", "_filled.json")
    filled_path = "ss-patient-input/fill-files/filled/" + os.path.basename(
        filled_path
    )  # Save in filled directory, if it exists
    with open(filled_path, "w", encoding="utf-8") as f_out:
        json.dump(filled_json, f_out, indent=4)

    print(f"Filled patient file saved to: {filled_path}")
    return filled_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fill missing fields in FHIR patient files."
    )
    parser.add_argument("path", help="Path to a patient JSON file.")
    args = parser.parse_args()

    if os.path.isdir(args.path):
        print(f"Validating multiple patient files in directory: {args.path}")
        modify_multiple_files(args.path)

    if os.path.isfile(args.path) and args.path.endswith(".json"):
        print(f"Validating single patient file: {args.path}")
        filled_json = modify_single_file(args.path)
        if filled_json:
            print("Successfully filled missing fields in the patient JSON.")
        else:
            print("Error: Failed to fill missing fields in the patient JSON.")
    else:
        print("Error: Please provide a valid JSON file.")
