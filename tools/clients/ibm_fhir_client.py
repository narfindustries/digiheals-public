#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for vista that can create patients and pull data
"""

import click
import json
import requests
from abstract_client import AbstractClient
import xml.etree.ElementTree as ET
from xml.dom import minidom

from xml.dom import minidom
import re

class IBMFHIRClient(AbstractClient):
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, fhir, base):
        """Constructor"""
        self.fhir = fhir
        self.base = base

    def export_patients(self, file_type='json'):
        """Calls the FHIR API to export all patients"""
        # TBD: XML capabilities
        header_text = "application/fhir+" + file_type
        headers = {"Accept": header_text}
        try:
            r = requests.get(
                f"{self.fhir}/{self.base}/Patient",
                headers=headers,
                timeout=100,
                verify=False,
                auth=("fhiruser", "change-password"),
            )
            if file_type == "json":
                response_data = r.json()
            else:
                response_data = r.text
            return (r.status_code, response_data)
        except Exception as e:
            return (-1, str(e))

    def export_patient(self, p_id, file_type):
        """Calls the FHIR API to export all patients"""
        header_text = "application/fhir+" + file_type
        headers = {"Accept": header_text}
        r = requests.get(
            f"{self.fhir}/{self.base}/Patient/{p_id}",
            headers=headers,
            timeout=100,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        if file_type == "json":
            response_data = r.json()
        else:
            response_data = r.text
        return (r.status_code, response_data)

    def __get_new_patient_id(self, before_data, file_type):
        """
        Get the patient ID by pulling full list of patients before and after
        """
        (status, after_data) = self.export_patients(file_type)
        if file_type == "json":
            if len(after_data["entry"]) == 1:
                return after_data["entry"][0]["resource"]["id"]

            for entry in after_data["entry"]:
                if entry not in before_data["entry"]:
                    return entry["resource"]["id"]
        else:
            print("####")
            before_root = ET.fromstring(before_data)
            after_root = ET.fromstring(after_data)
            after_entries = after_root.findall('.//{http://hl7.org/fhir}entry')
            before_entries = before_root.findall('.//{http://hl7.org/fhir}entry')

            if len(after_entries) == 1:
                return after_entries[0].find('.//{http://hl7.org/fhir}resource').find('.//{http://hl7.org/fhir}id').get('value')

            # If there are multiple entries, find the new one
            before_entry_ids = {entry.find('.//{http://hl7.org/fhir}resource').find('.//{http://hl7.org/fhir}id').get('value') for entry in before_entries}
            print(before_entry_ids)
            print("$$$$")
            for entry in after_entries:
                resource_id = entry.find('.//{http://hl7.org/fhir}resource').find('.//{http://hl7.org/fhir}id').get('value')
                print(resource_id)
                if resource_id not in before_entry_ids:
                    return resource_id

    def create_patient_fromfile(self, file, file_type):
        """Create a new patient from a FHIR JSON file"""
        (b_status, before_data) = self.export_patients(file_type)
        header_text = "application/fhir+" + file_type
        headers = {
            "Accept": header_text,
            "Content-Type": header_text,
        }
        if file_type == "json":
            data = json.dumps(data)
        r = requests.post(
            f"{self.fhir}/{self.base}/Patient",
            data=file.read(),
            timeout=10,
            headers=headers,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        patient_id = None
        if r.status_code == 201:
            # if file_type == "json":
            #     response = r.json()
            #     patient_id = response["id"]
            # else:
            #     response = r.text
            #     root = ET.fromstring(response)
            #     ns = {"fhir": "http://hl7.org/fhir"}
            #     patient_id_element = root.find("fhir:id", ns)
            #     if patient_id_element is not None:
            #         patient_id = patient_id_element.get("value")
        
            patient_id = self.__get_new_patient_id(before_data, file_type)
        return (patient_id, r)

    def create_patient(self, data, file_type):
        """Create a new patient from a FHIR JSON file"""
        (b_status, before_data) = self.export_patients(file_type)
        print(before_data)
        header_text = "application/fhir+" + file_type
        headers = {
            "Accept": header_text,
            "Content-Type": header_text,
        }
        if file_type == "json":
            data = json.dumps(data)
        r = requests.post(
            f"{self.fhir}/{self.base}/Patient",
            data=data,
            timeout=10,
            headers=headers,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        patient_id = None
        if r.status_code == 201:
            print("@@@@")
            print(r, r.content)
            # if file_type == "json":
            #     response = r.json()
            #     patient_id = response["id"]
            # else:
            #     response = r.text
            #     root = ET.fromstring(response)
            #     ns = {"fhir": "http://hl7.org/fhir"}
            #     patient_id_element = root.find("fhir:id", ns)
            #     if patient_id_element is not None:
            #         patient_id = patient_id_element.get("value")
            patient_id = self.__get_new_patient_id(before_data, file_type)
        return (patient_id, r)

    def step(self, step_number: int, data, file_type):
        """
        Called from the GoT scripts
        If its the first step, we just got a FHIR JSON file from Synthea.
        We must extract the patient data from it.
        If not, then we can import the file as is
        """
        patient_id = None
        response_json = None
        if step_number == 0:
            if file_type == "json":
                json_data = json.loads(data)
                patient_data = None
                for entry in json_data["entry"]:
                    if entry["resource"]["resourceType"] == "Patient":
                        patient_data = entry["resource"]
            else:
                # File type is XML
                tree = ET.ElementTree(ET.fromstring(data))
                root = tree.getroot()
                patient_data = None
                ns = {"fhir": "http://hl7.org/fhir"}  # Define namespace
                # Traverse XML tree to find Patient resource
                for entry in root.findall("fhir:entry", ns):
                    resource = entry.find("fhir:resource", ns)
                    if resource is not None:
                        patient = resource.find("fhir:Patient", ns)
                        if patient is not None:
                            patient_data = ET.tostring(patient, encoding="unicode")
            (patient_id, response_json) = self.create_patient(patient_data, file_type)
            print(patient_id)
        else:
            # This means we just got a full file from another server, simply upload it
            if file_type == "json":
                data["communication"] = [
                    {
                        "language": {
                            "coding": [
                                {
                                    "system": "urn:ietf:bcp:47",
                                    "code": "en-US",
                                    "display": "English (United States)",
                                }
                            ],
                            "text": "English (United States)",
                        }
                    }
                ]
                patient_data = data
            else:
                print(type(data))
                root = ET.fromstring(data)
                # Create the new communication element
                communication = ET.Element("communication")
                language = ET.SubElement(communication, "language")
                coding = ET.SubElement(language, "coding")

                system = ET.SubElement(coding, "system")
                system.set("value", "urn:ietf:bcp:47")

                code = ET.SubElement(coding, "code")
                code.set("value", "vi")

                display = ET.SubElement(coding, "display")
                display.set("value", "Vietnamese")

                text = ET.SubElement(language, "text")
                text.set("value", "Vietnamese")

                # Append the new communication element to the root
                root.append(communication)

                # Convert the tree back to a string
                updated_xml_data = ET.tostring(root, encoding='unicode')

                
                patient_data = updated_xml_data

                print(patient_data)
                
            (patient_id, response_json) = self.create_patient(patient_data, file_type)

        if patient_id is None:
            return (patient_id, {}, None)

        (status, export_response) = self.export_patient(patient_id, file_type)
        return (patient_id, {}, export_response)


@click.command()
@click.option("--file", type=click.File("r"))
def cli_options(file):
    """
    Extract command-line arguments to either create a new patient
    No arguments: exports all patients in a JSON form
    """
    client = IBMFHIRClient("https://localhost:8005", "fhir-server/api/v4")
    if file is None:
        status, response = client.export_patients()
        if status == 200:
            print(response.text)
        else:
            print(status)
    else:
        try:
            ET.parse(file)
            file_type = "xml"
        except ET.ParseError:
            file_type = "json"
        file = file.read()

        _, r = client.create_patient_fromfile(file, file_type)
        print(r.text)


if __name__ == "__main__":
    cli_options()
