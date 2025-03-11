import csv
import os

def parse_fhir_spec_csv(file_path):
    """Parse CSV file to extract all fields and their types."""
    metadata = {}
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                field, field_type = row
                metadata[field] = {"type": field_type}
    return metadata

def list_files_in_folder(folder_path):
    """List all file paths in the given folder."""
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths