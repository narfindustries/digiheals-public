"""
Create unit test for Synthea FHIR JSON file generation
"""

import pytest
import requests
import os
import time


def generate_fhir_file():
    """Create Synthea File"""
    r = requests.get("http://localhost:9000/", timeout=100)
    time.sleep(20)
    if r.status_code == 200:
        filename = r.json()["filename"]
        file_path = f"../../files/fhir/{filename}"
        file = open(file_path).read()
        return file, filename
    return None


@pytest.fixture
def clean_up_file():
    """Clean Up Generated Test File"""
    file_to_clean = []
    yield file_to_clean

    for filename in file_to_clean:
        synthea_cleanup = requests.get(f"http://localhost:9000/cleanup/{filename}")
        result = synthea_cleanup.json()
        if result["success"]:
            print(f"Successfully deleted test files - {filename}")


def test_generate_fhir_file_success(clean_up_file):
    """Call Synthea Generation"""
    file_content, filename = generate_fhir_file()
    if filename:
        clean_up_file.append(filename)

    assert file_content is not None
