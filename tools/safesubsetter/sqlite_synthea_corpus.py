"""
Script to build sqlite db with synthea patient data examples
"""

import json
import os
import sqlite3
import csv
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

RESOURCES_FOLDER = "output/resource"
TYPES_FOLDER = "output/types"


def parse_fhir_spec_csv(file_path):
    """Parse csv file to extract all fields and their types"""
    metadata = {}
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                field, field_type = row
                metadata[field] = {"type": field_type}
    return metadata


def create_table(conn, resource_type, metadata, table_type="resource"):
    """Create table for resource or type with metadata as columns"""
    cursor = conn.cursor()
    columns = [f'"{field}" TEXT' for field in metadata.keys() if field != "id"]
    columns.append('"source_file" TEXT')

    if table_type == "resource":
        sql_query = f"""
            CREATE TABLE IF NOT EXISTS "{resource_type}" (
                "id" TEXT PRIMARY KEY,
                {', '.join(columns)}
            )
        """
    else:
        sql_query = f"""
            CREATE TABLE IF NOT EXISTS "{resource_type}" (
                "id" integer PRIMARY KEY AUTOINCREMENT,
                {', '.join(columns)}
            )
        """

    cursor.execute(sql_query)
    conn.commit()


def process_field_value(value):
    """Process values in each field based on # of elements and return as string"""
    if isinstance(value, list) and len(value) == 1:
        return str(value[0])
    elif isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value) if value is not None else None


def insert_data(
    conn, file_path, resource_type, resource_data, metadata, types_folder, depth=0
):
    """
    Insert value into table. For depth > 0, create table, then insert value into new table.
    Max depth == 1
    """
    if depth > 1:
        return  # Stop processing nested structures beyond depth 1

    cursor = conn.cursor()
    resource_id = resource_data.get("id")
    cursor.execute(f"SELECT 1 FROM {resource_type} WHERE id = ?", (resource_id,))
    if cursor.fetchone():
        print(
            f"{resource_type} with id {resource_id} already exists. Skipping insertion."
        )
        return

    if resource_id is None:  # If field is of type and not resource
        columns = ["source_file"]
        values = [file_path]
    else:
        columns = ["id", "source_file"]
        values = [resource_id, file_path]

    for field, details in metadata.items():
        value = resource_data.get(field)
        if (
            details.get("type")
            and details["type"][0].isupper()
            and os.path.exists(os.path.join(types_folder, f"{details['type']}.csv"))
            and depth < 1
        ):
            nested_type = details["type"]
            nested_spec_file = os.path.join(types_folder, f"{nested_type}.csv")

            nested_metadata = parse_fhir_spec_csv(nested_spec_file)

            # Ensure the nested table exists before inserting data
            create_table(conn, nested_type, nested_metadata, "type")
            if isinstance(value, list):
                for nested_item in value:
                    insert_data(
                        conn,
                        file_path,
                        nested_type,
                        nested_item,
                        nested_metadata,
                        types_folder,
                        depth + 1,
                    )
            elif isinstance(value, dict):
                insert_data(
                    conn,
                    file_path,
                    nested_type,
                    value,
                    nested_metadata,
                    types_folder,
                    depth + 1,
                )
        else:
            columns.append(field)
            values.append(process_field_value(value))

    placeholders_insert = ", ".join(["?"] * len(values))
    insert_query = f"INSERT INTO {resource_type} ({', '.join(columns)}) VALUES ({placeholders_insert})"
    cursor.execute(insert_query, values)
    conn.commit()


def process_synthea_json(file_path, resources_folder, types_folder):
    """Read Synthea file and process the fields"""
    conn = sqlite3.connect(
        "synthea_corpus_main.db"
    )  # Each thread gets its own connection

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        resource_spec_file = os.path.join(resources_folder, f"{resource_type}.csv")
        if os.path.exists(resource_spec_file):
            metadata = parse_fhir_spec_csv(resource_spec_file)
            create_table(conn, resource_type, metadata)
            insert_data(
                conn, file_path, resource_type, resource, metadata, types_folder
            )

    conn.close()


def list_files_in_folder(folder_path):
    """List all file paths in the given folder."""
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add Synthea patient files to db using multithreading."
    )
    parser.add_argument(
        "folder_path",
        type=str,
        help="Path to the folder containing Synthea patient files.",
    )
    args = parser.parse_args()

    file_paths = list_files_in_folder(args.folder_path)

    num_threads = os.cpu_count()
    # Using ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(
                process_synthea_json, file, RESOURCES_FOLDER, TYPES_FOLDER
            ): file
            for file in file_paths
        }

        for i, future in enumerate(as_completed(futures)):
            print(f"Processed file {i + 1}/{len(file_paths)}: {futures[future]}")
