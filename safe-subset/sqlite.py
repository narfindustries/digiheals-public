import json
import os
import sqlite3
import csv

def parse_fhir_spec_csv(file_path):
    metadata = {}
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                field, field_type = row
                metadata[field] = {'type': field_type}
    return metadata

def create_table(conn, resource_type, metadata):
    cursor = conn.cursor()
    columns = []
    for field, details in metadata.items():
        if field != 'id':  # Avoid duplicate 'id' field
            columns.append(f"{field} TEXT")
    columns.append("source_file TEXT")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {resource_type} (
            id TEXT PRIMARY KEY,
            {', '.join(columns)}
        )
    """)
    conn.commit()

def process_field_value(value):
    if isinstance(value, list) and len(value) == 1:
        return str(value[0])
    elif isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value) if value is not None else None

def insert_data(conn, resource_type, resource_data, metadata, types_folder, depth=0):
    if depth > 1:
        return  # Stop processing nested structures beyond depth 1

    cursor = conn.cursor()
    resource_id = resource_data.get('id')
    cursor.execute(f"SELECT 1 FROM {resource_type} WHERE id = ?", (resource_id,))
    if cursor.fetchone():
        print(f"{resource_type} with id {resource_id} already exists. Skipping insertion.")
        return

    columns = ['id', 'source_file']
    values = [resource_id, SAMPLE_JSON]

    print(metadata)

    for field, details in metadata.items():
        value = resource_data.get(field)
        if details.get('type') and details['type'][0].isupper() and os.path.exists(os.path.join(types_folder, f"{details['type']}.csv")) and depth < 1:
            nested_type = details['type']
            nested_spec_file = os.path.join(types_folder, f"{nested_type}.csv")
            if os.path.exists(nested_spec_file):
                nested_metadata = parse_fhir_spec_csv(nested_spec_file)
                print(nested_metadata)
                # Ensure the nested table exists before inserting data
                create_table(conn, nested_type, nested_metadata)
                if isinstance(value, list):
                    for nested_item in value:
                        insert_data(conn, nested_type, nested_item, nested_metadata, types_folder, depth + 1)
                elif isinstance(value, dict):
                    insert_data(conn, nested_type, value, nested_metadata, types_folder, depth + 1)
        else:
            columns.append(field)
            values.append(process_field_value(value))

    placeholders = ", ".join(["?"] * len(values))
    cursor.execute(f"INSERT INTO {resource_type} ({', '.join(columns)}) VALUES ({placeholders})", values)
    conn.commit()

def process_synthea_json(file_path, resources_folder, types_folder):
    conn = sqlite3.connect("synthea.db")

    with open(file_path, 'r') as f:
        data = json.load(f)

    for entry in data.get('entry', []):
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')

        resource_spec_file = os.path.join(resources_folder, f"{resource_type}.csv")
        if os.path.exists(resource_spec_file):
            metadata = parse_fhir_spec_csv(resource_spec_file)
            create_table(conn, resource_type, metadata)
            insert_data(conn, resource_type, resource, metadata, types_folder)

    conn.close()

RESOURCES_FOLDER = "resource"
TYPES_FOLDER = "type"
SAMPLE_JSON = "Sample_safe_subset.json"
process_synthea_json(SAMPLE_JSON, RESOURCES_FOLDER, TYPES_FOLDER)
