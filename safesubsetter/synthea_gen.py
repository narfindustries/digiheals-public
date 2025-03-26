"""Script to generate N synthea patient files"""
import os
import sys
import requests


for i in range(0,1000):
    r = requests.get("http://localhost:9000/", timeout=100)
    file_type = "json"
    if r.status_code == 200:
        filename = r.json()["filename"]

        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
        # Change synthea file directory based on location of directory
        file = open(os.path.join(base_path, f"synthea-config-test/fhir/{filename}"), encoding='utf-8').read()

        print(f"Successfully created file for {filename}")
    else:
        print("File creation failed from Synthea")
        print(r)
        sys.exit(1)
