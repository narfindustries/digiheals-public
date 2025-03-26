"""Script to run validator.py on output patient files from FHIR server"""
import os

from validator import validate_patient_json
import db_syn

DB_PATH = os.path.join(os.path.dirname(__file__), "syn_server.db")
db = db_syn.Database(DB_PATH)

# Directories
input_dir = "Synthea-patient-data-all/input-og"
output_base_dir = "Synthea-patient-data-all/output-test"
servers = ["blaze", "hapi", "IBM", "iris", "vista"]

# Loop through each patient file in input directory
for patient_filename in os.listdir(input_dir):
    input_file_path = os.path.join(input_dir, patient_filename)
    
    # Validate original patient file
    og_valid = str(validate_patient_json(input_file_path))

    # Dictionary to hold server validation results
    server_validations = {}

    # Validate corresponding patient files for each server
    for server in servers:
        server_patient_filename = f"{server}_{patient_filename}"
        server_file_path = os.path.join(output_base_dir, server, server_patient_filename)

        if os.path.exists(server_file_path):
            server_validations[server] = str(validate_patient_json(server_file_path))
        else:
            server_validations[server] = str([])  # Handle missing file gracefully
    print(server_validations)
    # Insert validation results into database
    db.insert_syn_file_record(
        patient_file=patient_filename,
        og_file_valid=og_valid,
        blaze_valid=server_validations["blaze"],
        hapi_valid=server_validations["hapi"],
        ibm_valid=server_validations["IBM"],
        iris_valid=server_validations["iris"],
        vista_valid=server_validations["vista"]
    )