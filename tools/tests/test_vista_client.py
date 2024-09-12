"""
Create unit tests for Vista Client
"""

import json
import sys
import pytest

sys.path.append("../clients")
from vista_client import VistaClient


@pytest.fixture(scope="module")
def vista_client():
    """Create FHIR Client"""
    fhir = "http://localhost:8002"
    base = "api"
    client = VistaClient(fhir, base)
    yield client


@pytest.fixture(scope="module")
def patient_data():
    """Read Patient Data File"""
    with open(
        "./test_files/Luigi346_Quitzon246_bd63337a-ea66-952d-b02d-4a79db2ca530.json",
        "r", encoding='utf-8'
    ) as file:
        return file.read()


@pytest.fixture(scope="module")
def patient_id(vista_client, patient_data):
    """Import Patient Data to server to get Patient ID"""
    patient_id, response = vista_client.create_patient(patient_data)
    assert response.status_code == 201
    assert patient_id is not None
    return patient_id


class TestVistaClient:

    def test_create_patient_fromfile(self, patient_id):
        """Test create_patient_fromfile and create_patient"""
        assert patient_id is not None

    def test_export_patients(self, vista_client):
        """Test export_patients"""
        status_code, response = vista_client.export_patients()
        assert status_code == 200
        assert isinstance(response, dict)

    def test_export_patient(self, vista_client, patient_id):
        """Test export_patient"""
        status_code, response = vista_client.export_patient(patient_id)
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
    def test_step(self, vista_client, step_number, filename):
        """Test for steps 0 and 1"""
        file_type = "json"  # Only JSON support is available for Vista currently
        if step_number == 0:
            with open(filename, "r", encoding='utf-8') as file:
                patient_id, response_json, export_response = vista_client.step(
                    step_number, file, file_type
                )
        else:
            with open(filename, "r", encoding='utf-8') as file:
                data = json.load(file)
                patient_id, response_json, export_response = vista_client.step(
                    step_number, data, "json"
                )

        if patient_id is None and "Duplicate SSN" in response_json.get(
            "loadMessage", ""
        ):
            assert (
                "-1^Duplicate SSN" in response_json["loadMessage"]
            ), "Duplicate SSN should be reported"
            print("Duplicate Patient Record Found")
        else:
            assert patient_id is not None
            assert isinstance(response_json, dict)
            assert isinstance(export_response, dict)


if __name__ == "__main__":
    pytest.main()
