#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for ibm that can create patients and pull data
"""
import json
import click
import requests
from abstract_client import AbstractClient


class IBMFHIRClient(AbstractClient):
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, fhir, base):
        """Constructor"""
        self.fhir = fhir
        self.base = base

    def export_patients(self):
        """Calls the FHIR API to export all patients"""
        try:
            r = requests.get(
                f"{self.fhir}/{self.base}/Bundle",
                timeout=100,
                verify=False,
                auth=("fhiruser", "change-password"),
            )
            response = r.json()
            return (r.status_code, response)
        except Exception as e:
            return (-1, str(e))

    def export_patient(self, p_id):
        """Calls the FHIR API to export patients with given ID"""
        r = requests.get(
            f"{self.fhir}/{self.base}/Bundle/{p_id}",
            timeout=100,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        response = r.json()
        return (r.status_code, response)

    def __get_new_patient_id(self, before_json):
        """
        Get the patient ID by pulling full list of patients before and after
        """
        (_, after_json) = self.export_patients()

        if len(after_json["entry"]) == 1:
            return after_json["entry"][0]["resource"]["id"]

        for entry in after_json["entry"]:
            if entry not in before_json["entry"]:
                return entry["resource"]["id"]

    def create_patient_fromfile(self, file):
        """Create a new patient from a FHIR JSON file"""
        (_, before_json) = self.export_patients()
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"{self.fhir}/{self.base}/Bundle",
            data=file.read(),
            timeout=10,
            headers=headers,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        patient_id = None
        if r.status_code == 201:
            patient_id = self.__get_new_patient_id(before_json)
        return (patient_id, r)

    def create_patient(self, data):
        """Create a new patient from a FHIR JSON file"""
        (_, before_json) = self.export_patients()
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"{self.fhir}/{self.base}/Bundle",
            data=data,
            timeout=10,
            headers=headers,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        patient_id = None
        if r.status_code == 201:
            patient_id = self.__get_new_patient_id(before_json)
        return (patient_id, r)

    def step(self, step_number: int, data, file_type):
        """
        Called from the GoT scripts
        If its the first step, we just got a FHIR JSON file from Synthea.
        We must extract the patient data from it.
        If not, then we can import the file as is
        """
        patient_id = None
        if step_number == 0:
            try:
                patient_data = json.loads(data)
                (patient_id, _) = self.create_patient(json.dumps(patient_data))
            except json.JSONDecodeError:
                raise click.BadParameter("Malformed input json file.")
        else:
            # This means we just got a full file from another server, simply upload it
            if file_type == "json":
                data["type"] = "transaction"
                data = json.dumps(data)

            (patient_id, _) = self.create_patient(data)

        if patient_id is None:
            return (patient_id, {}, None)

        (_, export_response) = self.export_patient(patient_id)
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
        _, r = client.create_patient_fromfile(file)
        print(r.text)


if __name__ == "__main__":
    cli_options()
