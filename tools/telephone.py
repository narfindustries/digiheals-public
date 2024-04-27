#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Skeleton for the Telephone.py script to go through multiple targets
"""
import click
from click_option_group import (
    optgroup,
    OptionGroup,
    RequiredMutuallyExclusiveOptionGroup,
)
import sys
import json
import requests

sys.path.append("./clients")

from blaze_client import BlazeClient
from hapi_client import HapiClient
from ibm_fhir_client import IBMFHIRClient
from vista_client import VistaClient
from db import create_nodes

config = {
    "vista": ("http://localhost:8002", "api"),
    "ibm": ("https://localhost:8005", "fhir-server/api/v4"),
    "hapi": ("http://localhost:8004", "fhir"),
    "blaze": ("http://localhost:8006", "fhir"),
}
chain_config = OptionGroup(
    "Configure all chains", help="How to configure all enumerated chains"
)


@click.command()
@click.option("--chain-length", "chain_length", default=3, type=int)
@optgroup.group(
    "Either generate a file or provide a command-line argument",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Group description",
)
@optgroup.option("--file", type=click.File("r"))
@optgroup.option("--generate", "generate", is_flag=True, default=False)
@optgroup.group(
    "Either use a chain or generate all chains",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Group description",
)
@optgroup.option(
    "--chain",
    "-c",
    multiple=True,
    type=click.Choice(["vista", "ibm", "hapi", "blaze"]),
)
@optgroup.option("--all-chains", "all_chains", is_flag=True, default=False)
def cli_options(chain_length, file, generate, chain, all_chains):
    """Command line options for the telephone.py script
    Vista takes a different format (Bundle Resource) as input, whereas others require a patient
    """
    vista_client = VistaClient(config["vista"][0], config["vista"][1])
    ibm_client = IBMFHIRClient(config["ibm"][0], config["ibm"][1])
    hapi_client = HapiClient(config["hapi"][0], config["hapi"][1])
    blaze_client = BlazeClient(config["blaze"][0], config["blaze"][1])

    functions = {
        "vista": vista_client.step,
        "ibm": ibm_client.step,
        "hapi": hapi_client.step,
        "blaze": blaze_client.step,
    }

    # Create nodes in the neo4j database for all the servers we use
    # It won't create duplicate nodes for the servers
    # We add additional nodes to denote the end of a chain and how many keys are present
    create_nodes(list(config.keys()) + ["synthea", "file", "end"])

    # Generate a new FHIR JSON file
    if generate:
        r = requests.get("http://localhost:9000/", timeout=100)
        if r.status_code == 200:
            filename = r.json()["filename"]
            # overwrite the file variable
            file = open(f"../files/fhir/{filename}")
            print(f"Successfully created file for {filename}")

    if all_chains:
        print(all_chains, chain_length)
    else:
        # all chains not specified, so we specified specific hops
        for step_number, step in enumerate(chain):
            (patient_id, response_json_1, response_json_2) = functions[step](
                step_number, file
            )
            if patient_id is None:
                print(
                    f"Chain terminated at step {step_number} {step} {response_json_1}"
                )
                sys.exit(1)
            file = response_json_2
            print(f"{step_number} {step} {json.dumps(file)}")


if __name__ == "__main__":
    cli_options()
