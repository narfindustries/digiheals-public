"""
Create unit tests for Vista Client
"""

import pytest
import json
import sys

sys.path.append("../clients")
from ibm_fhir_client import IBMFHIRClient


@pytest.fixture(scope="module")
def ibm_fhir_client():
    """Create FHIR Client"""
    fhir = "https://localhost:8005"
    base = "fhir-server/api/v4"
    client = IBMFHIRClient(fhir, base)
    yield client


@pytest.fixture(scope="module")
def patient_data():
    """Read Patient Data File"""
    with open(
        "./test_files/Adelaide981_Osinski784_580f24ad-3303-7f6a-309e-bf6d767f7046.json",
        "r",
    ) as file:
        json_data = json.loads(file.read())
        for entry in json_data["entry"]:
            if entry["resource"]["resourceType"] == "Patient":
                return entry["resource"]


@pytest.fixture(scope="module")
def patient_id(ibm_fhir_client, patient_data):
    """Import Patient Data to server to get Patient ID"""
    patient_id, response = ibm_fhir_client.create_patient(json.dumps(patient_data))
    assert response.status_code == 201
    assert patient_id is not None
    return patient_id


class TestIBMFHIRClient:

    def test_create_patient_fromfile(self, patient_id):
        """Test create_patient_fromfile and create_patient"""
        assert patient_id is not None

    def test_export_patients(self, ibm_fhir_client):
        """Test export_patients"""
        status_code, response = ibm_fhir_client.export_patients()
        assert status_code == 200
        assert isinstance(response, dict)

    def test_export_patient(self, ibm_fhir_client, patient_id):
        """Test export_patient"""
        status_code, response = ibm_fhir_client.export_patient(patient_id)
        assert status_code == 200
        assert isinstance(response, dict)

    @pytest.mark.parametrize(
        "step_number, filename",
        [
            (
                0,
                "./test_files/Abbie917_Frami345_ffa07c38-1f19-6336-9952-9152a6c882c9.json",
            ),
            (1, "./test_files/Anglea614_Blanche121_ibm_output.json"),
        ],
    )
    def test_step(self, ibm_fhir_client, step_number, filename):
        """Test for steps 0 and 1"""
        if step_number == 0:
            with open(filename, "r") as file:
                patient_id, response_json, export_response = ibm_fhir_client.step(
                    step_number, file.read()
                )
        else:
            with open(filename, "r") as file:
                data = json.load(file)
                patient_id, response_json, export_response = ibm_fhir_client.step(
                    step_number, data
                )

        assert patient_id is not None
        assert isinstance(response_json, dict)
        assert isinstance(export_response, dict)


if __name__ == "__main__":
    pytest.main()
