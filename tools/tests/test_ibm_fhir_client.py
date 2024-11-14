"""
Create unit tests for IBM Client
"""

import json
import sys
import pytest

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
def patient_data_json():
    """Read Patient Data File"""
    with open(
        "./test_files/Gordon377_Smith67_e5339c99-4895-1005-25c8-b02c3607d11c.json",
        "r",
        encoding="utf-8",
    ) as file:
        json_data = json.loads(file.read())
        return json_data


@pytest.fixture(scope="module")
def patient_data_xml():
    """Read Patient Data XML File"""
    with open(
        "./test_files/Tawanda156_Marielle507_Jacobson885_7674fc84-c574-e4eb-c809-507b185b110.xml",
        "r",
        encoding="utf-8",
    ) as file:
        return file.read()


@pytest.fixture(scope="module", params=["json", "xml"])
def patient_id(ibm_fhir_client, patient_data_json, patient_data_xml, request):
    """Import Patient Data to server to get Patient ID for both JSON and XML"""
    if request.param == "json":
        patient_data = patient_data_json
    else:
        patient_data = patient_data_xml

    patient_id, response = ibm_fhir_client.create_patient(patient_data, request.param)
    assert response.status_code == 201
    assert patient_id is not None
    return patient_id, request.param


class TestIBMFHIRClient:

    def test_create_patient_fromfile(self, patient_id):
        """Test create_patient_fromfile and create_patient"""
        # Patient ID already created through fixture
        patient_id_value, _ = patient_id  # Unpacking the tuple
        assert patient_id_value is not None

    def test_export_patients(self, ibm_fhir_client):
        """Test export_patients"""
        status_code, response = ibm_fhir_client.export_patients()
        assert status_code == 200
        assert isinstance(response, dict)  # Response is in json by default

    def test_export_patient(self, ibm_fhir_client, patient_id):
        """Test export_patient"""
        patient_id_value, file_type = patient_id  # Unpacking the tuple
        status_code, response = ibm_fhir_client.export_patient(
            patient_id_value, file_type
        )
        assert status_code == 200
        if file_type == "json":
            assert isinstance(response, dict)
        else:
            assert isinstance(response, str)

    @pytest.mark.parametrize(
        "step_number, filename, file_type",
        [
            (
                0,
                "./test_files/Allan198_Lockman863_a2f3765a-dbec-5702-bb12-0426ddf4b535.json",
                "json",
            ),
            (
                1,
                "./test_files/Step1_Leonel449_Ryan260_1e00a484-5de7-ebe7-4a81-3573e055531b.json",
                "json",
            ),
            (
                0,
                "./test_files/Leanne251_Rice937_5bf2b528-4162-16a3-e418-f0f6adb47b41.xml",
                "xml",
            ),
            (
                1,
                "./test_files/Step1_Shelby741_Koss676_320924f3-d18a-c5ed-19d1-ff2326f362bc.xml",
                "xml",
            ),
        ],
    )
    def test_step(self, ibm_fhir_client, step_number, filename, file_type):
        """Test for steps 0 and 1"""
        if step_number == 0:
            with open(filename, "r", encoding="utf-8") as file:
                patient_id, response_json, export_response = ibm_fhir_client.step(
                    step_number, file.read(), file_type
                )
        else:
            with open(filename, "r", encoding="utf-8") as file:
                data = file.read() if file_type == "xml" else json.load(file)
                patient_id, response_json, export_response = ibm_fhir_client.step(
                    step_number, data, file_type
                )

        assert patient_id is not None
        if file_type == "xml":
            resp_type = str
        else:
            resp_type = dict
        assert isinstance(response_json, resp_type)
        assert isinstance(export_response, resp_type)
