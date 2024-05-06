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
       return file, file_path
   return None


@pytest.fixture
def clean_up_file():
    """Clean Up Generated Test File
       TO DO: Files don't seem to have permission to be deleted.    
    """
    file_to_clean = []
    yield file_to_clean

    for file_path in file_to_clean:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:
            print(f"Cannot delete {file_path}: {e}")


def test_generate_fhir_file_success(clean_up_file):
    """Call Synthea Generation"""
    file_content, file_path = generate_fhir_file()
    if file_path:
        clean_up_file.append(file_path) 
    
    assert file_content is not None

