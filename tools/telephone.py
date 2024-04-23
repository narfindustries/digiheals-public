#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Skeleton for the Telephone.py script to go through multiple targets
"""
import click
import sys
import json

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
@click.option(
    "--chain",
    "-c",
    required=True,
    multiple=True,
    type=click.Choice(["vista", "ibm", "hapi"]),
)
def cli_options(file, chain):
    """Command line options for the telephone.py script
    Vista takes a different format (Bundle Resource) as input, whereas others require a patient
    """
    vista_client = VistaClient(config["vista"][0], config["vista"][1])
    ibm_client = IBMFHIRClient(config["ibm"][0], config["ibm"][1])
    hapi_client = HapiClient(config["hapi"][0], config["hapi"][1])

    functions = {
        "vista": vista_client.step,
        "ibm": ibm_client.step,
        "hapi": hapi_client.step,
    }

    for step_number, step in enumerate(chain):
        (patient_id, response_json_1, response_json_2) = functions[step](
            step_number, file
        )
        if patient_id is None:
            print(f"Chain terminated at step {step_number} {step} {response_json_1}")
            sys.exit(1)
        file = response_json_2
        print(file)


if __name__ == "__main__":
    cli_options()
