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


class IBMFHIRClient(AbstractClient):
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, fhir, base):
        """Constructor"""
        self.fhir = fhir
        self.base = base

    def export_patients(self):
        """Calls the FHIR API to export all patients"""
        r = requests.get(
            f"{self.fhir}/{self.base}/Patient",
            timeout=100,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        return r

    def export_patient(self, p_id):
        """Calls the FHIR API to export all patients"""
        r = requests.get(
            f"{self.fhir}/{self.base}/Patient/{p_id}",
            timeout=100,
            verify=False,
            auth=("fhiruser", "change-password"),
        )
        return r

    def create_patient_fromfile(self, file):
        """Create a new patient from a FHIR JSON file"""
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
            auth=("fhiruser", "change-password"),
        )
        print(r.text)
        return r

    def create_patient(self, data):
        """Create a new patient from a FHIR JSON file"""
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
            auth=("fhiruser", "change-password"),
        )
        print(r.text)
        return r


@click.command()
@click.option("--file", type=click.File("r"))
def cli_options(file):
    """
    Extract command-line arguments to either create a new patient
    No arguments: exports all patients in a JSON form
    """
    client = IBMFHIRClient("https://localhost:8005", "fhir-server/api/v4")
    if file is None:
        response = client.export_patients()
        if response.status_code == 200:
            print(response.json())
    else:
        print(client.create_patient(file).json())


if __name__ == "__main__":
    cli_options()
