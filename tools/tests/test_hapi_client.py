"""
Create unit tests for Hapi Client
"""

import pytest
import json
import xml.etree.ElementTree as ET
import sys

sys.path.append("../clients")
from hapi_client import HapiClient


# Define fixture with scope limited to duration of module
@pytest.fixture(scope="module")
def hapi_client():
    """Create FHIR Client"""
    fhir = "http://localhost:8004"
    base = "fhir"
    client = HapiClient(fhir, base)
    yield client


@pytest.fixture(scope="module")
def patient_data_json():
    """Read Patient Data JSON File"""
    with open(
        "./test_files/Adelaide981_Osinski784_580f24ad-3303-7f6a-309e-bf6d767f7046.json",
        "r",
    ) as file:
        json_data = json.loads(file.read())
        for entry in json_data["entry"]:
            if entry["resource"]["resourceType"] == "Patient":
                return entry["resource"]


@pytest.fixture(scope="module")
def patient_data_xml():
    """Read Patient Data XML File"""
    with open(
        "./test_files/Elaina826_Dayna943_Marvin195_b25b43b3-3284-0867-dfdb-f8f9a32fbc91.xml",
        "r",
    ) as file:
        tree = ET.parse(file)
        root = tree.getroot()
        ns = {"fhir": "http://hl7.org/fhir"}
        # Traverse XML tree to find Patient resource
        for entry in root.findall("fhir:entry", ns):
            resource = entry.find("fhir:resource", ns)
            if resource is not None:
                patient = resource.find("fhir:Patient", ns)
                if patient is not None:
                    return ET.tostring(patient, encoding="utf-8")


@pytest.fixture(scope="module", params=["json", "xml"])
def patient_id(hapi_client, patient_data_json, patient_data_xml, request):
    """Import Patient Data to server to get Patient ID for both JSON and XML"""
    if request.param == "json":
        patient_data = patient_data_json
    else:
        patient_data = patient_data_xml

    patient_id, response = hapi_client.create_patient(patient_data, request.param)
    assert response.status_code == 201
    assert patient_id is not None
    return patient_id, request.param


class TestHapiClient:

    def test_create_patient_fromfile(self, patient_id):
        """Test create_patient_fromfile and create_patient"""
        # Patient ID already created through fixture
        patient_id_value, _ = patient_id  # Unpacking the tuple
        assert patient_id_value is not None

    def test_export_patients(self, hapi_client):
        """Test export_patients"""
        status_code, response = hapi_client.export_patients()
        assert status_code == 200
        assert isinstance(response, dict)  # Response is in json by default

    def test_export_patient(self, hapi_client, patient_id):
        """Test export_patient"""
        patient_id_value, file_type = patient_id  # Unpacking the tuple
        status_code, response = hapi_client.export_patient(patient_id_value, file_type)
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
                "./test_files/Abbie917_Frami345_ffa07c38-1f19-6336-9952-9152a6c882c9.json",
                "json",
            ),
            (1, "./test_files/Anglea614_Blanche121_ibm_output.json", "json"),
            (
                0,
                "./test_files/Elaina826_Dayna943_Marvin195_b25b43b3-3284-0867-dfdb-f8f9a32fbc91.xml",
                "xml",
            ),
            (1, "./test_files/Miguel815_Alejandro916_blaze_step_1_output.xml", "xml"),
        ],
    )
    def test_step(self, hapi_client, step_number, filename, file_type):
        """Test for steps 0 and 1"""
        if step_number == 0:
            with open(filename, "r", encoding="utf-8") as file:
                patient_id, response_json, export_response = hapi_client.step(
                    step_number, file.read(), file_type
                )
        else:
            with open(filename, "r", encoding="utf-8") as file:
                data = file.read() if file_type == "xml" else json.load(file)
                patient_id, response_json, export_response = hapi_client.step(
                    step_number, data, file_type
                )

        assert patient_id is not None
        if file_type == "xml":
            response_json = response_json.text
            resp_type = str
        else:
            resp_type = dict
        assert isinstance(response_json, resp_type)
        assert isinstance(export_response, resp_type)


if __name__ == "__main__":
    pytest.main()
