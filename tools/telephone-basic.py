#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#

import json
import sys
import click

sys.path.append("./clients")

from hapi_client import HapiClient
from ibm_fhir_client import IBMFHIRClient
from vista_client import VistaClient

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
    (vista_patient_id, step1a_response) = vista_client.create_patient_fromfile(file)
    if vista_patient_id is None:
        chain_terminated = True
        print(step1a_response.json())
        sys.exit(1)

    print(f"Vista Import {step1a_response} {vista_patient_id}")

    (status_1b, vista_patient_response) = vista_client.export_patient(vista_patient_id)
    if status_1b != 200:
        chain_terminated = True
        print(vista_patient_response)
        sys.exit(1)

    print(f"Vista Export {status_1b} {vista_patient_id}")

    # Step 2 starts here
    (hapi_patient_id, step2a_response) = hapi_client.create_patient(
        json.dumps(vista_patient_response)
    )
    if hapi_patient_id is None:
        chain_terminated = True
        print(step2a_response.json())
        sys.exit(1)

    print(f"HAPI Import {step2a_response} {hapi_patient_id}")

    (status_2a, hapi_patient_response) = hapi_client.export_patient(hapi_patient_id)
    if status_2a != 200:
        chain_terminated = True
        print(hapi_patient_response)
        sys.exit(1)

    print(f"HAPI Export {status_2a} {hapi_patient_id}")

    hapi_patient_response["communication"] = [
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

    # Step 3 starts here
    (ibm_patient_id, step3a_response) = ibm_client.create_patient(
        json.dumps(hapi_patient_response)
    )
    if step3a_response.status_code != 201:
        chain_terminated = True
        print(step3a_response.json())
        sys.exit(1)

    print(f"IBM Import {step3a_response} {ibm_patient_id}")

    ibm_patient_response = None
    (status_3b, ibm_patient_response) = ibm_client.export_patient(ibm_patient_id)

    print(f"IBM Export {status_3b} {ibm_patient_response}")


if __name__ == "__main__":
    cli_options()
