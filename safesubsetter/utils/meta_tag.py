"""Script to inject the patient file with a meta tag"""
import os
import json
import argparse
import sys

def inject_meta_tag(file_path, tag_code):
    """Inject tag_code into meta section of patient file"""
    
    # Read the existing JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in {str(file_path)}: {e}")
            sys.exit(1)

    # Add or update the meta tag
    data['meta'] = {
        "tag": [
            {
                "system": "http://example.org/fhir/tags",
                "code": f"{tag_code}",
                "display": f"{tag_code} stored collection bundle"
            }
        ]
    }

    # Write the changes back to the same file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject tag into patient file")
    parser.add_argument(
        "path",
        help="Path to a patient JSON file",
    )
    parser.add_argument("--tag",required=True, help="Tag to inject into the patient file")
    args = parser.parse_args()

    inject_meta_tag(args.path, args.tag)
    

# # Path to the filled folder
# folder_path = 'ss-patient-input/fill-files/filled'

# count = 1 
# # Loop through all files in the folder
# for filename in os.listdir(folder_path):
#     if filename.endswith('_filled.json'):
#         file_path = os.path.join(folder_path, filename)
#         file_stem = filename.replace('_filled.json', '')

#         # Read the existing JSON
#         with open(file_path, 'r', encoding='utf-8') as f:
#             try:
#                 data = json.load(f)
#             except json.JSONDecodeError as e:
#                 print(f"Error decoding JSON in {filename}: {e}")
#                 continue

#         # Add or update the meta tag
#         data['meta'] = {
#             "tag": [
#                 {
#                     "system": "http://example.org/fhir/tags",
#                     "code": f"{file_stem}-stored-collection",
#                     "display": f"{file_stem} stored collection bundle"
#                 }
#             ]
#         }

#         # Write the changes back to the same file
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)

#         print(f"Updated {count}: {filename}")
#         count += 1