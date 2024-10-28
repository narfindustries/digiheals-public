"""
Create unit tests for Vista Client
"""

import json
import sys
import pytest

from references_modify import modify_references_in_json

sys.path.append("../clients")
from iris_client import IrisClient


@pytest.fixture(scope="module")
def iris_client():
    """Create FHIR Client"""
    fhir = "http://localhost:8007"
    base = "fhir/r4"
    client = IrisClient(fhir, base)
    yield client


@pytest.fixture(scope="module")
def patient_data():
    """Read Patient Data File"""
    with open(
        "./test_files/Wilbert25_Dare640_0b28086d-1670-37a6-b07d-4b581f948b5d.json",
        "r",
        encoding="utf-8",
    ) as file:
        json_data = modify_references_in_json(json.loads(file.read()))
        return json_data


@pytest.fixture(scope="module")
def patient_id(iris_client, patient_data):
    """Import Patient Data to server to get Patient ID"""
    patient_id, response = iris_client.create_patient(patient_data)
    assert response.status_code == 201
    assert patient_id is not None
    return patient_id


class TestIrisClient:

    def test_create_patient_fromfile(self, patient_id):
        """Test create_patient_fromfile and create_patient"""
        assert patient_id is not None

    def test_export_patients(self, iris_client):
        """Test export_patients"""
        status_code, response = iris_client.export_patients()
        assert status_code == 200
        assert isinstance(response, dict)

    def test_export_patient(self, iris_client, patient_id):
        """Test export_patient"""
        status_code, response = iris_client.export_patient(patient_id)
        assert status_code == 200
        assert isinstance(response, dict)

    @pytest.mark.parametrize(
        "step_number, filename",
        [
            (
                0,
                "./test_files/Suzanne628_Jesus702_Stehr398_1589ce57-c816-e5d4-744e-a0e9899bab32.json",
            ),
            (1, "./test_files/Monty345_Borer986_ibm_step1.json"),
        ],
    )
    def test_step(self, iris_client, step_number, filename):
        """Test for steps 0 and 1"""
        file_type = "json"  # Only JSON support is available for iris currently
        if step_number == 0:
            with open(filename, "r", encoding="utf-8") as file:
                patient_id, response_json, export_response = iris_client.step(
                    step_number,
                    modify_references_in_json(json.loads(file.read())),
                    file_type,
                )
        else:
            with open(filename, "r", encoding="utf-8") as file:
                data = modify_references_in_json(json.load(file))
                outer_data = json.loads(data)
                patient_id, response_json, export_response = iris_client.step(
                    step_number, outer_data, file_type
                )

        assert patient_id is not None
        assert isinstance(response_json, dict)
        assert isinstance(export_response, dict)


if __name__ == "__main__":
    pytest.main()
