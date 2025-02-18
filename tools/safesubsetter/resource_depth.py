""" Find max depth for each resource type"""
import os
import csv

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

def find_max_depth(spec_file, depth, visited_files_per_path, chain_path):
    """
    Recursively find the chain with the maximum depth.
    """
    if spec_file in visited_files_per_path:
        return depth - 1, chain_path[:-1]  # Prevent infinite recursion and recursion in loop, we do depth-1, to exclude the file already visited

    visited_files_per_path.add(spec_file)
    metadata = parse_fhir_spec_csv(spec_file)
    max_depth = depth
    max_depth_chain = chain_path

    for _, details in metadata.items():
        if "type" in details and details["type"][0].isupper():  # Check if type is a nested type
            nested_type = details["type"]

            # Find the folder the nested file belongs to
            resource_nested_spec_file = os.path.join(RESOURCES_FOLDER, f"{nested_type}.csv")
            type_nested_spec_file = os.path.join(TYPES_FOLDER, f"{nested_type}.csv")
            nested_spec_file = resource_nested_spec_file if os.path.exists(resource_nested_spec_file) else type_nested_spec_file

            if os.path.exists(nested_spec_file):
                new_chain_path = chain_path + [nested_type]
                nested_depth, nested_chain = find_max_depth(
                    nested_spec_file, depth + 1, visited_files_per_path.copy(), new_chain_path
                )
                # Check recursive output from child with parent depth and chain and replace max_depth
                if nested_depth > max_depth:
                    max_depth = nested_depth
                    max_depth_chain = nested_chain

    return max_depth, max_depth_chain

def list_files_in_folder(folder_path):
    """List all file paths in the given folder."""
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths

# Process all resource files
resource_files = list_files_in_folder(RESOURCES_FOLDER)
max_depth_across_resources = 0

for resource_file in resource_files:
    print(f"Processing: {resource_file}")

    # Set depth=1, empty set for visited files in path, and initial chain path
    max_depth, max_depth_chain = find_max_depth(resource_file, 1, set(), [os.path.basename(resource_file).split(".")[0]])

    max_depth_across_resources = max(max_depth, max_depth_across_resources)

    # Print chain with max depth for this file
    print(f"{resource_file}: Max Depth = {max_depth}")
    print(" -> ".join(max_depth_chain), "\n")

print(f"Max depth across all resources: {max_depth_across_resources}")
