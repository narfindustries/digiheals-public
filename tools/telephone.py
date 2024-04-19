#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""

"""
import sys
import click
import json

sys.path.append("./clients")
from vista_client import VistaClient
from ibm_fhir_client import IBMFHIRClient
from hapi_client import HapiClient

config = {
    "vista": ("http://localhost:8002", "api"),
    "ibm": ("https://localhost:8005", "fhir-server/api/v4"),
    "hapi": ("http://localhost:8004", "fhir"),
}


@click.command()
@click.option("--file", type=click.File("r"), required=True)
def cli_options(file):
    """
    Extract command-line arguments to either create a new patient
    Step 1a: Send the Synthea-generated file through Vista
    Step 1b: Store the Patient ID and GET /Patient/{id}
    Step 2a: Send the response through HAPI FHIR
    Step 2b: Store the Patient ID and GET /Patient/{id}
    Step 3a: Send response through IBM FHIR
    Step 3b: Store the Patient ID and GET /Patient/{id}
    """

    vista_client = VistaClient(config["vista"][0], config["vista"][1])
    ibm_client = IBMFHIRClient(config["ibm"][0], config["ibm"][1])
    hapi_client = HapiClient(config["hapi"][0], config["hapi"][1])

    chain_terminated = False  # Set to true whenever we need to terminate the chain
    # Step 1
    vista_patient_id = None
    step1a_response = vista_client.create_patient_fromfile(file)
    if step1a_response.status_code == 201:
        r = step1a_response.json()
        if r["loadStatus"] == "loaded" and r.get("icn"):
            vista_patient_id = r["icn"]
        else:
            chain_terminated = True
    else:
        chain_terminated = True

    # Add a gate here to ensure that the chain is not terminated before starting 1a
    if chain_terminated:
        print(step1a_response.json())
        sys.exit(1)

    vista_patient_response = None
    step1b_response = vista_client.export_patient(vista_patient_id)
    print(step1b_response)
    if step1b_response.status_code == 200:
        vista_patient_response = step1b_response.json()
    else:
        chain_terminated = True
        print(step1b_response.json())
        sys.exit(1)

    # Step 2 starts here
    step2a_response = hapi_client.create_patient(json.dumps(vista_patient_response))
    print(step2a_response)
    hapi_patient_id = None
    if step2a_response.status_code == 201:
        r = step2a_response.json()
        hapi_patient_id = r["id"]
    else:
        chain_terminated = True
        print(step2a_response.json())
        sys.exit(1)

    hapi_patient_response = None
    step2b_response = hapi_client.export_patient(hapi_patient_id)
    print(step2b_response)
    if step2b_response.status_code == 200:
        hapi_patient_response = step2b_response.json()
    else:
        chain_terminated = True
        print(step2b_response.json())
        sys.exit(1)

    hapi_patient_response["communication"] =[{
        "language": {
            "coding": [{
                "system": "urn:ietf:bcp:47",
                "code": "en-US",
                "display": "English (United States)"
            }],
            "text": "English (United States)"
        }
    }]

    print(json.dumps(hapi_patient_response))
    # Step 3 starts here
    step3a_response = ibm_client.create_patient(json.dumps(hapi_patient_response))
    print(step3a_response)
    ibm_patient_id = None
    if step3a_response.status_code != 201:
        chain_terminated = True
        print(step3a_response.json())
        sys.exit(1)

    ibm_patient_response = None
    step3b_response = ibm_client.export_patients()
    print(step3b_response)
    if step3b_response.status_code == 200:
        ibm_patient_response = step3b_response.json()
    else:
        chain_terminated = True
        print(step3b_response.json())
        sys.exit(1)

if __name__ == "__main__":
    cli_options()
