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


class HapiClient(AbstractClient):
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, fhir, base):
        """Constructor"""
        self.fhir = fhir
        self.base = base

    def export_patients(self):
        """Calls the FHIR API to export all patients"""
        try:
            r = requests.get(f"{self.fhir}/{self.base}/Patient", timeout=100)
            return (r.status_code, r.json())
        except Exception as e:
            return (-1, str(e))

    def export_patient(self, p_id):
        """Calls the FHIR API to export all patients"""
        r = requests.get(
            f"{self.fhir}/{self.base}/Patient/{p_id}", timeout=100, verify=False
        )
        response_json = r.json()
        return (r.status_code, response_json)

    def create_patient_fromfile(self, file):
        """Create a new patient from a FHIR JSON file"""
        patient_id = None
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"{self.fhir}/{self.base}/Patient",
            data=file.read(),
            timeout=10,
            headers=headers,
            verify=False,
        )
        if r.status_code == 201:
            response = r.json()
            patient_id = response["id"]
        return (patient_id, r)

    def create_patient(self, data):
        """Create a new patient from a FHIR JSON file"""
        patient_id = None
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"{self.fhir}/{self.base}/Patient",
            data=data,
            timeout=10,
            headers=headers,
            verify=False,
        )
        if r.status_code == 201:
            response = r.json()
            patient_id = response["id"]
        return (patient_id, r)

    def step(self, step_number: int, data):
        """
        Called from the GoT scripts
        If its the first step, we just got a FHIR JSON file from Synthea.
        We must extract the patient data from it.
        If not, then we can import the file as is
        """
        patient_id = None
        response_json = None
        if step_number == 0:
            json_data = json.loads(data)
            patient_data = None
            for entry in json_data["entry"]:
                if entry["resource"]["resourceType"] == "Patient":
                    patient_data = entry["resource"]
            (patient_id, response_json) = self.create_patient(json.dumps(patient_data))
        else:
            # This means we just got a full file from another server, simply upload it
            (patient_id, response_json) = self.create_patient(json.dumps(data))

        if patient_id is None:
            return (patient_id, response_json.json(), None)

        (status, export_response) = self.export_patient(patient_id)
        return (patient_id, response_json.json(), export_response)


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
        _, r = client.create_patient_fromfile(file)
        print(r.text)

if __name__ == "__main__":
    cli_options()
