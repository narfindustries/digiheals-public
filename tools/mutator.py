"""Module to mutate each field for a given patient data"""

import argparse
import os
import json
import csv
import exrex
import rfc3986
import copy
import re
import time
import docker 

from telephone import telephone_function
from validator import validate_patient_json
import db_mut

RESOURCES_FOLDER = "output/resource"
TYPES_FOLDER = "output/types"

docker_client = docker.from_env()
ibm_request_count = 0

FHIR_SERVERS = ["vista"] #["iris", "ibm", "blaze", "hapi", "vista"]

DB_PATH = os.path.join(os.path.dirname(__file__), "safe_subset.db")
db = db_mut.Database(DB_PATH)

# xhtml type has been ignored, as there is no regex defined for it
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
     'id' : {'type':'string', 'regex':'[A-Za-z0-9\-\.]{1,64}'},
     'largeString': {'type':'largestring', 'value':"A" * 1024},
     'largeInt': {'type':'largeinteger', 'value':2**200},
     'largeFloat': {'type':'largefloat', 'value':1.7976931348623157E+308}
    }

class EfficientSSNGenerator:
    """Random SSN generator class"""
    def __init__(self):
        self.current_num = 1010001
    
    def get_next_ssn(self):
        """Increments to return the next randomly generated SSN"""
        while self.current_num <= 999999999:
            ssn_str = f"{self.current_num:09d}"
            area = ssn_str[:3]
            group = ssn_str[3:5]
            serial = ssn_str[5:]
            
            if area == '666':
                self.current_num = 667000000
                continue
            elif area.startswith('9'):
                raise ValueError("Reached invalid 900+ area numbers")
            
            if group == '00':
                self.current_num += 1000
                continue
                
            if serial == '0000':
                self.current_num += 1
                continue
                
            if area in ['000', '734', '749', '772']:
                self.current_num += 1000000
                continue
                
            result = f"{area}-{group}-{serial}"
            self.current_num += 1
            return result
            
        raise ValueError("Exhausted all possible SSNs")
    

ssn_generator = EfficientSSNGenerator()

def ssn_gen():
    """Function to generate a unique, valid SSN"""
    return ssn_generator.get_next_ssn()


def restart_container(container_name):
    """Stop and then start a Docker container by name."""
    docker_client = docker.from_env()
    for container in docker_client.containers.list():
        if container_name.lower() in container.name.lower():
            print(f"Stopping container: {container.name}")
            container.stop()
            time.sleep(20) 

            print(f"Starting container: {container.name}")
            container.start()
            time.sleep(420) # Takes about 7 min for servers to start responding


def mutate_and_send(nested_field, old_value, old_type, file_path, path, og_patient_data):
    """Mutate a field and send it to FHIR server using function in telephone.py."""
    for new_type, type_regex_info in FHIR_TYPES.items():
        if new_type == old_type:
            continue  # Skip original type
        else: 
            if new_type in ["largeInt","largeString","largeFloat"]:
                new_value = type_regex_info["value"]
            else:
                new_regex = type_regex_info["regex"]
                new_value = exrex.getone(new_regex)
                
                if type_regex_info["type"] == "integer":
                    new_value = int(new_value)

                if type_regex_info["type"] == "decimal":
                    new_value = float(new_value)

                if type_regex_info["type"] == "boolean":
                    new_value = bool(new_value)

                # Use custom uri,url,canonical value as the regex generator generates emtpy string
                if new_type in ["uri","url","canonical"]:
                    new_value = "http://hl7.org/fhir/StructureDefinition/geolocation"

            
            for server in FHIR_SERVERS:
                modified_patient = modify_json_field(copy.deepcopy(og_patient_data), path, new_value)

                if server == "vista":
                    leaf_path = "Patient_0.identifier"
                    new_ssn_value = ssn_gen()
                    modified_patient_vista = modify_json_field(modified_patient, leaf_path, new_ssn_value, modify_ssn=True)
                    modified_patient = modified_patient_vista

                temp_file = "temp_patient_vista.json"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(modified_patient, f, indent=4)
                
                # Calling validator on modified patient input
                ip_validity_err_list = validate_patient_json("temp_patient_vista.json")
                ip_validity = True if len(ip_validity_err_list) == 0 else False
                status, msg = send_to_fhir_server(temp_file, server)
                # Once we know that the status is True, it means the export patient was successful
                validate_and_store_response(file_path, path, old_type, old_value, new_type, new_value, server, status, msg, ip_validity, ip_validity_err_list)
            

def modify_json_field(og_patient_data, leaf_path, new_value=None, modify_ssn=False):
    """Modify the JSON by replacing only the specified leaf node."""
    list_index = int(leaf_path.split('.')[0].split('_')[1])
    resourceType = leaf_path.split('.')[0].split('_')[0]
    
    new_data = copy.deepcopy(og_patient_data)  # Create a deep copy to avoid modifying original data
    current = new_data["entry"][list_index]["resource"]

    if resourceType == current.get("resourceType", ""):  
        # Modify SSN field for Vista
        if modify_ssn and "identifier" in current:
            for value in current["identifier"]:
                    if value.get("type", {}).get("text") == "Social Security Number":
                        value["value"] = new_value
            return new_data

        keys = re.split(r'\.|\[|\]', leaf_path) 
        keys = [key for key in keys if key] # Removing empty strings

        for i, key in enumerate(keys):
            if key == "contained":
                # Keys post this are for a new ResourceType
                nested_keys = keys[i+1:]
                nested_func_replace(current[key], nested_keys, new_value)
                return new_data
            
            if '_' in key:
                continue

            if key.isdigit():
                key = int(key)
            
            if i == len(keys) - 1:
                current[key] = new_value  # Update the value at the final key
            else:
                current = current[key]  # Traverse deeper

        return new_data
    

def nested_func_replace(data, keys, new_value):
    """ Updates values inside a nested ResourceType in the form of a list"""
    for i in keys:
        if '-' in i:
            index = int(i.split('-')[0])
            nested_key = i.split('-')[1]
            if nested_key == data[index]["resourceType"]:
                current = data[index]
                for j, key in enumerate(keys[1:]):

                    if key.isdigit(): 
                        key = int(key)
                    
                    if j == len(keys) - 2:
                        current[key] = new_value  
                    else:
                        current = current[key]
                return 


def send_to_fhir_server(patient_file, server):
    """Send modified patient data to server through telephone.py func"""
    global ibm_request_count

    if server == "ibm" or server == "iris":
        ibm_request_count += 1

        # Restart after every 120 requests
        if ibm_request_count % 120 == 0:
            print(f"120 {server} requests reached. Restarting {server} container.")
            restart_container(server)

    try:
        _ = telephone_function(1, patient_file, False, [server], False, "json", "full")
        file_path = "temp_response_vista.json"
        if os.path.isfile(file_path):        
            return True, "File created successfully"
    except Exception as e:
        return False, f"Error: {e}"
    return False, "Unknown error occurred"


def resp_type_check(file, leaf_path):
    """Return the type and value from response patient file for the leaf path"""
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
 
    list_index = int(leaf_path.split('.')[0].split('_')[1])
    resourcetype = leaf_path.split('.')[0].split('_')[0]
    print(leaf_path)
    current = data["entry"][list_index]["resource"]

    if resourcetype == current.get("resourceType", ""):
        keys = re.split(r'\.|\[|\]', leaf_path)
        keys = [key for key in keys if key]
        for i, key in enumerate(keys):
            if key == "contained":
                nested_keys = keys[i+1:]
                resp_type_val = resp_nested_type(current[key], nested_keys)
                return resp_type_val
            
            if '_' in key:
                continue

            if key.isdigit():
                key = int(key)
            
            if i == len(keys) - 1:
                if key in current:
                    return (type(current[key]).__name__, current[key])
                else:
                    return ("N/A", f"Key {key} missing")
            else:
                if key in current:
                    current = current[key]
                else:
                    return ("N/A", f"Key {key} missing")
                


def resp_nested_type(data, keys):
    """ Return the type and value from response inside a nested ResourceType in the form of a list"""
    for i in keys:
        if '-' in i:
            index = int(i.split('-')[0])
            nested_key = i.split('-')[1]
            if nested_key == data[index]["resourceType"]:
                current = data[index]
                for j, key in enumerate(keys[1:]):

                    if key.isdigit():
                        key = int(key)
                    
                    if j == len(keys) - 2:
                        if key in current:
                            return (type(current[key]).__name__, current[key])
                        else:
                            return ("N/A", "Key missing")
                    else:
                        if key in current:
                            current = current[key]
                        else:
                            return ("N/A", f"Key {key} missing")
            

def validate_and_store_response(patient_file_path, path, old_type, old_value, new_type, new_value, server, status, msg, ip_validity, ip_validity_err_list):
    """Validate the responses from servers and insert into SQLite db"""
    resp_file = "temp_response_vista.json"
    error_file = "temp_error_vista.json"

    if status:
        # Server responded
        op_validity_err_list = validate_patient_json(resp_file)
        op_validity = not op_validity_err_list
        resp_type, resp_value = resp_type_check(resp_file, path)

    else:
        # Error from server
        op_validity = False
        op_validity_err_list = []
        if os.path.exists(error_file):
            with open(error_file, "r", encoding="utf-8") as f:
                msg = str(json.load(f))
        else:
            msg = "N/A"
        resp_type = resp_value = "N/A"
    
    print(path, old_type, old_value, new_type, new_value, server, status, msg, op_validity, op_validity_err_list)

    db.insert_safe_subset_record(
        patient_file=patient_file_path,
        leaf_node_path=path,
        old_type=old_type,
        old_value=str(old_value),
        new_type=new_type,
        new_value=str(new_value),
        resp_type = resp_type,
        resp_value=str(resp_value),
        server=server,
        response_status=status,
        error_message=msg,
        ip_validity=ip_validity,
        ip_validity_error=str(ip_validity_err_list),
        op_validity=op_validity,
        op_validity_error=str(op_validity_err_list)
    )
    remove_temp_files()


def validate_nested_field(nested_field, value, metadata, recursive_metadata, file_path, path, og_patient_data):
    """Validate a nested field and handle recursion if needed."""
    if nested_field in metadata:
        field_type = metadata[nested_field]["type"]
        if isinstance(value, list):
            for i, item in enumerate(value):
                new_path = f"{path}[{i}]"
                mutate_and_send(nested_field, item, field_type, file_path, new_path, og_patient_data)
        else:
            mutate_and_send(nested_field, value, field_type, file_path, path, og_patient_data)

    if nested_field in recursive_metadata:
        recursive_traversal(value, recursive_metadata[nested_field]["type"], file_path, path, og_patient_data)


def recursive_traversal(patient_data, field_type, file_path, path, og_patient_data):
    """Recursively traverse nested patient data up to 12 levels deep."""
    if field_type == "Resource":
        double_resource_call(patient_data, file_path, path, og_patient_data)
        return

    resourcetype_csv = os.path.join(TYPES_FOLDER, f"{field_type}.csv")
    metadata, recursive_metadata = parse_fhir_spec_csv(resourcetype_csv)

    if isinstance(patient_data, dict):
        for nested_field in list(patient_data.keys()):
            new_path = f"{path}.{nested_field}"
            value = patient_data[nested_field]
            validate_nested_field(nested_field, value, metadata, recursive_metadata, file_path, new_path, og_patient_data)

    elif isinstance(patient_data, list):
        for i, item in enumerate(patient_data):
            new_path = f"{path}[{i}]"
            if isinstance(item, dict):
                for nested_field, value in item.items():
                    new_path_1 = f"{new_path}.{nested_field}"
                    validate_nested_field(nested_field, value, metadata, recursive_metadata, file_path, new_path_1, og_patient_data)


def double_resource_call(patient_data, file_path, path, og_patient_data):
    """Process resources within another resourceType in the patient data."""
    if isinstance(patient_data, list):
        for i, res in enumerate(patient_data):
            resource_type = res.get("resourceType")
            if not resource_type:
                continue
            
            new_path = f"{path}.{i}-{resource_type}"
            resourcetype_csv = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
            metadata, recursive_metadata = parse_fhir_spec_csv(resourcetype_csv)
            
            for nested_field, value in res.items():
                if nested_field != "resourceType":
                    nested_path = f"{new_path}.{nested_field}"
                    validate_nested_field(nested_field, value, metadata, recursive_metadata, file_path, nested_path, og_patient_data)


def remove_temp_files():
    """Remove the temporary patient and error files that are created."""
    temp_files = [
            "temp_response_vista.json",
            "temp_patient_vista.json",
            "temp_error_vista.json"
        ]
    
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)

    print("Removed temp files.")


def validate_patient_json_file(file_path):
    """Validate a single patient JSON file."""
    
    with open(file_path, "r", encoding="utf-8") as f:
        patient_data = json.load(f)

    remove_temp_files()

    if not patient_data:
        return
    
    patient_resource_types = set(['Patient','Location','Encounter','Practitioner','PractitionerRole','Organization','CareTeam','CarePlan'])

    for i, entry in enumerate(patient_data["entry"]):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if not resource_type:
            continue
        # Check if resourcetype is in the set, if not proceed, else skip
        if resource_type in patient_resource_types:
            continue
        else: 
            patient_resource_types.add(resource_type)

        path = f"{resource_type}_{i}"
        print(path)

        resourcetype_csv = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
        metadata, recursive_metadata = parse_fhir_spec_csv(resourcetype_csv)

        for nested_field in list(resource.keys()):
            if nested_field != "resourceType":
                new_path = f"{path}.{nested_field}"
                validate_nested_field(nested_field, resource[nested_field], metadata, recursive_metadata, file_path, new_path, patient_data)


def parse_fhir_spec_csv(file_path):
    """Parse CSV file to extract all fields and their types as metadata."""
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


def validate_multiple_patients(directory_path):
    """Validate all patient JSON files in a directory and output a list of errors."""
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            print(f"Processing {filename}")
            start_time = time.time()
            validate_patient_json_file(os.path.join(directory_path, filename))
            end_time = time.time()

            elapsed_time = (end_time - start_time)/60
            print(f"Time elapsed: {elapsed_time} min")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mutate FHIR patient files.")
    parser.add_argument("path", help="Path to a patient JSON file or a directory containing multiple JSON files.")
    args = parser.parse_args()

    if os.path.isdir(args.path):
        print(f"Validating multiple patient files in directory: {args.path}")
        validate_multiple_patients(args.path)

    if os.path.isfile(args.path) and args.path.endswith(".json"):
        print(f"Validating single patient file: {args.path}")
        start_time = time.time()
        validate_patient_json_file(args.path)
        end_time = time.time()

        elapsed_time = (end_time - start_time)/60
        print(f"Time elapsed: {elapsed_time} min")
    else:
        print("Error: Invalid path. Please provide a valid JSON file or a directory containing JSON files.")
