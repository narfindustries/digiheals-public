#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for vista that can create patients and pull data
"""

import click
import requests


class VistaClient:
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, vehu, fhir):
        """Constructor"""
        self.vehu = vehu
        self.fhir = fhir

    def export(self):
        """Calls the FHIR API to export all patients"""
        r = requests.get(f"{self.fhir}/api/Patient", timeout=100)
        return r

    def create(self, file):
        """Calls the MUMPS API to create a new patient from a FHIR JSON"""
        r = requests.post(f"{self.vehu}/addpatient", data=file.read(), timeout=10)
        return r.status_code


@click.command()
@click.option("--create", default=False, is_flag=True)
@click.option("--file", type=click.File("r"))
def cli_options(create, file):
    """
    Extract command-line arguments to either create a new patient
    No arguments: exports all patients in a JSON form
    """
    client = VistaClient("http://localhost:9080", "http://localhost:8002")
    if not create:
        response = client.export()
        if response.status_code == 200:
            print(response.json())
    else:
        if file is None:
            print("Needs the --file argument")
        else:
            print(client.create(file))


if __name__ == "__main__":
    cli_options()
