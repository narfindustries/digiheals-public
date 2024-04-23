#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for vista that can create patients and pull data
"""

import click
import requests
from abstract_client import AbstractClient


class VistaClient(AbstractClient):
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, fhir, base):
        """Constructor"""
        self.vehu = "http://localhost:9080"
        self.fhir = fhir
        self.base = base

    def export_patients(self):
        """Calls the FHIR API to export all patients"""
        r = requests.get(f"{self.fhir}/{self.base}/Patient", timeout=100)
        return (r.status_code, r.json())

    def export_patient(self, p_id):
        """Calls the FHIR API to export all patients"""
        r = requests.get(f"{self.fhir}/{self.base}/Patient/{p_id}", timeout=100)
        return (r.status_code, r.json())

    def create_patient_fromfile(self, file):
        """Calls the MUMPS API to create a new patient from a FHIR JSON"""
        r = requests.post(f"{self.vehu}/addpatient", data=file.read(), timeout=100)
        patient_id = None
        if r.status_code == 201:
            response = r.json()
            if response["loadStatus"] == "loaded" and response.get("icn"):
                patient_id = response["icn"]
        return (patient_id, r)

    def create_patient(self, data):
        """Calls the MUMPS API to create a new patient from a FHIR JSON"""
        r = requests.post(f"{self.vehu}/addpatient", data=data, timeout=100)
        patient_id = None
        if r.status_code == 201:
            response = r.json()
            if response["loadStatus"] == "loaded" and response.get("icn"):
                patient_id = response["icn"]
        return (patient_id, r)

    def step(self, step_number: int, data):
        """
        Called from the GoT scripts
        If its the first step, we just got a FHIR JSON file from Synthea.
        If not, then we need to bundle it in a FHIR JSON with the resourceType: Bundle
        """
        patient_id = None
        response_json = None
        if step_number == 0:
            # This means we just got a full file, simply upload it
            (patient_id, response_json) = self.create_patient_fromfile(data)
        else:
            # Got a JSON from another FHIR server
            pass
        if patient_id is None:
            # Creating the patient failed
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
    client = VistaClient("http://localhost:8002", "api")
    if file is None:
        response = client.export_patients()
        if response.status_code == 200:
            print(response.json())
        else:
            print(response.status_code)
    else:
        print(client.create_patient_fromfile(file).json())


if __name__ == "__main__":
    cli_options()
