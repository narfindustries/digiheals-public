#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for vista that can create patients and pull data
"""

import json
import click
import requests
from abstract_client import AbstractClient
from defusedxml.ElementTree import fromstring, tostring, parse, ParseError


class HapiClient(AbstractClient):
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, fhir, base):
        """Constructor"""
        self.fhir = fhir
        self.base = base

    def export_patients(self):
        """Calls the FHIR API to export all patients"""
        # TBD: XML capabilities
        try:
            r = requests.get(f"{self.fhir}/{self.base}/Bundle", timeout=100)
            return (r.status_code, r.json())
        except Exception as e:
            return (-1, str(e))

    def export_patient(self, p_id, file_type):
        """Calls the FHIR API to export all patients"""
        header_text = "application/fhir+" + file_type
        headers = {"Accept": header_text}
        r = requests.get(
            f"{self.fhir}/{self.base}/Bundle/{p_id}",
            headers=headers,
            timeout=100,
            verify=False,
        )
        if file_type == "json":
            response_data = r.json()
        else:
            response_data = r.text
        return (r.status_code, response_data)

    def create_patient_fromfile(self, file, file_type):
        """Create a new patient from a FHIR XML/JSON file"""
        patient_id = None
        header_text = "application/fhir+" + file_type
        headers = {
            "Accept": header_text,
            "Content-Type": header_text,
        }
        r = requests.post(
            f"{self.fhir}/{self.base}/Bundle",
            data=file.read(),
            timeout=10,
            headers=headers,
            verify=False,
        )
        if r.status_code == 201:
            if file_type == "json":
                response = r.json()
                patient_id = response["id"]
            else:
                response = r.text
                root = fromstring(response)
                ns = {"fhir": "http://hl7.org/fhir"}
                patient_id_element = root.find("fhir:id", ns)
                if patient_id_element is not None:
                    patient_id = patient_id_element.get("value")
        return (patient_id, r)

    def create_patient(self, data, file_type):
        """Create a new patient from a FHIR XML/JSON file"""
        patient_id = None
        header_text = "application/fhir+" + file_type
        headers = {
            "Accept": header_text,
            "Content-Type": header_text,
        }
        if file_type == "json":
            data["type"] = "collection"
            data = json.dumps(data)
        else:
            ns = {"fhir": "http://hl7.org/fhir"}
            data = data.strip()
            root = fromstring(data)
            type_element = root.find("fhir:type", ns)
            if type_element is not None:
                type_element.set("value", "collection")
                data = tostring(root, encoding="utf-8")

        r = requests.post(
            f"{self.fhir}/{self.base}/Bundle",  # /$everything returns Bundle type
            data=data,
            timeout=10,
            headers=headers,
            verify=False,
        )
        if r.status_code == 201:
            if file_type == "json":
                response = r.json()
                patient_id = response["id"]
            else:
                response = r.text
                root = fromstring(response)
                ns = {"fhir": "http://hl7.org/fhir"}
                patient_id_element = root.find("fhir:id", ns)
                if patient_id_element is not None:
                    patient_id = patient_id_element.get("value")

        return (patient_id, r)

    def step(self, step_number: int, data, file_type):
        """
        Called from the GoT scripts
        If its the first step, we just got a FHIR JSON file from Synthea.
        We must extract the patient data from it.
        If not, then we can import the file as is
        """
        patient_id = None
        response_data = None
        if step_number == 0:
            if file_type == "json":
                try:
                    patient_data = json.loads(data)
                except json.JSONDecodeError:
                    raise click.BadParameter("Malformed input json file.")
            else:
                # File type is XML
                patient_data = data
            (patient_id, response_data) = self.create_patient(patient_data, file_type)
        else:
            # This means we just got a full file from another server, simply upload it
            (patient_id, response_data) = self.create_patient(data, file_type)

        if patient_id is None:
            return_response = (
                response_data.json() if file_type == "json" else response_data
            )
            return (patient_id, return_response, None)

        (_, export_response) = self.export_patient(patient_id, file_type)

        return_response = response_data.json() if file_type == "json" else response_data
        return (patient_id, return_response, export_response)


@click.command()
@click.option("--file", type=click.File("r"))
def cli_options(file):
    """
    Extract command-line arguments to either create a new patient
    No arguments: exports all patients in a JSON form
    """
    client = HapiClient("http://localhost:8004", "fhir")
    if file is None:
        status, response = client.export_patients()
        if status == 200:
            print(response.text)
        else:
            print(status)
    else:
        try:
            parse(file)
            file_type = "xml"
        except ParseError:
            file_type = "json"
        file = file.read()

        _, r = client.create_patient_fromfile(file, file_type)
        print(r.text)


if __name__ == "__main__":
    cli_options()
