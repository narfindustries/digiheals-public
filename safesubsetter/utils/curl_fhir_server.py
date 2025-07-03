""" Script to test the FHIR servers output for all files in a specific folder."""

import subprocess
import os

folder_path = "ss-patient-input/fill-files/filled"

# Loop over all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)

        curl_command_ibm = [
            "curl",
            "-k",
            "-u",
            "fhiruser:change-password",
            "-X",
            "POST",
            "https://localhost:9443/fhir-server/api/v4/Bundle",
            "-H",
            "Content-Type: application/fhir+json",
            "-d",
            f"@{file_path}",
        ]

        curl_command_iris = [
            "curl",
            "-u",
            "_system:SYS",
            "-X",
            "POST",
            "http://localhost:8007/fhir/r4/Bundle",
            "-H",
            "Content-Type: application/fhir+json",
            "-d",
            f"@{file_path}",
        ]

        curl_command_blaze = [
            "curl",
            "-X",
            "POST",
            "http://localhost:8006/fhir/Bundle",
            "-H",
            "Content-Type: application/fhir+json",
            "-d",
            f"@{file_path}",
        ]

        curl_command_vista = [
            "curl",
            "-X",
            "POST",
            "http://localhost:9080/addpatient",
            "-H",
            "Content-Type: application/fhir+json",
            "-d",
            f"@{file_path}",
        ]

        curl_command_hapi = [
            "curl",
            "-X",
            "POST",
            "http://localhost:8004/fhir/Bundle",
            "-H",
            "Content-Type: application/fhir+json",
            "-d",
            f"@{file_path}",
        ]

        result = subprocess.run(curl_command_vista, capture_output=True, text=True)

        if result.stdout.strip():
            print(f"Response for {filename}: {result.stdout.strip()}")
            print("\n")
