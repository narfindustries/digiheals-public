#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for vista that can create patients and pull data
"""

import click
import requests
import json
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
        try:
            r = requests.get(f"{self.fhir}/{self.base}/Patient", timeout=100)
            return (r.status_code, r.json())
        except Exception as e:
            return (-1, str(e))

    def export_patient(self, p_id):
        """Calls the FHIR API to export all patients"""
        r = requests.get(f"{self.vehu}/showfhir", timeout=100, params={"ien": p_id})
        if r.status_code == 200:
            for entry in r.json()["entry"]:
                if entry["resource"]["resourceType"] == "Patient":
                    return (r.status_code, entry["resource"])
        try:
            return (r.status_code, r.json())
        except Exception:
            return (r.status_code, {})

    def create_patient_fromfile(self, file):
        """Calls the MUMPS API to create a new patient from a FHIR JSON"""
        r = requests.post(f"{self.vehu}/addpatient", data=file.read(), timeout=100)
        patient_id = None
        if r.status_code == 201:
            response = r.json()
            if response["loadStatus"] == "loaded" and response.get("ien"):
                patient_id = response["ien"]
        return (patient_id, r)

    def create_patient(self, data):
        """Calls the MUMPS API to create a new patient from a FHIR JSON"""
        r = requests.post(f"{self.vehu}/addpatient", data=data, timeout=100)
        patient_id = None
        if r.status_code == 201:
            response = r.json()
            if response["status"] == "ok" and response.get("ien"):
                patient_id = response["ien"]
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
            (patient_id, response_json) = self.create_patient(data)
        else:
            # Got a JSON from another FHIR server
            data = {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [{"resource": data}],
            }
            (patient_id, response_json) = self.create_patient(json.dumps(data))
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
