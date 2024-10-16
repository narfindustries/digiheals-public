#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Skeleton for the Telephone.py script to go through multiple targets
"""
import os
import sys
import uuid
import copy
import configparser
import requests

import db
from cli_options import add_chain_options

import click
from click_option_group import OptionGroup

sys.path.append("./clients")
from blaze_client import BlazeClient
from hapi_client import HapiClient
from ibm_fhir_client import IBMFHIRClient
from vista_client import VistaClient

neo4j_env = os.getenv("COMPOSE_PROFILES", "neo4jDev")

config = configparser.ConfigParser()
# Dynamically load directory where script is located - as its called from tests and also from run_scripts.py
dir_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(dir_path, "config.ini")
config.read(config_path)


config = {
    "vista": (config["DEFAULT"]["fhir-vista"], config["DEFAULT"]["fhir-vista-target"]),
    "hapi": (config["DEFAULT"]["hapi-fhir"], config["DEFAULT"]["hapi-fhir-target"]),
    "ibm": (config["DEFAULT"]["ibm-fhir"], config["DEFAULT"]["ibm-fhir-target"]),
    "blaze": (config["DEFAULT"]["blaze"], config["DEFAULT"]["blaze-target"]),
}

vista_client = VistaClient(config["vista"][0], config["vista"][1])
ibm_client = IBMFHIRClient(config["ibm"][0], config["ibm"][1])
hapi_client = HapiClient(config["hapi"][0], config["hapi"][1])
blaze_client = BlazeClient(config["blaze"][0], config["blaze"][1])

client_map = {
    "vista": vista_client,
    "ibm": ibm_client,
    "hapi": hapi_client,
    "blaze": blaze_client,
}


def validate_options(file_type, chain, all_chains):
    """Validate the combination of options."""
    if file_type.lower() == "xml" and (
        all_chains or any(c in chain for c in ["ibm", "vista"])
    ):
        raise click.BadParameter(
            "Combination not possible: --type xml with -c ibm or vista, or --all-chains."
        )


def check_connection(chain=None):
    """
    Send requests to all the servers to ensure they are up and returning 200s

    Parameters:
    - chain (tuple): Optional. A list of server names to check. If None, checks all servers.
    """
    if chain is not None and len(chain) > 0:
        clients = [client_map[x] for x in chain]
        client_names = chain
    else:
        clients = [vista_client, ibm_client, hapi_client, blaze_client]
        client_names = ["vista", "ibm", "hapi", "blaze"]

    for iterator, client in enumerate(map(lambda x: x.export_patients(), clients)):
        try:
            if not 200 <= client[0] < 300:  # TO DO: Handle this differently
                print(f"{client_names[iterator]} server not up. Exiting.")
                sys.exit(1)
        except Exception as e:
            print(f"{client_names[iterator]} exiting with error {e}")
            sys.exit(1)

    try:
        if neo4j_env == "neo4jDev":
            port = "7474"
        else:
            port = "7475"
        neo4j_req = requests.get(f"http://localhost:{port}")
        print(f"neo4j server responded with code: {neo4j_req.status_code}")
    except ConnectionResetError as e:
        print(f"{e}: Error starting neo4j.")
        sys.exit(1)

    try:
        synthea_req = requests.get("http://localhost:9000/status")
        print(f"Synthea server responded with code: {synthea_req.status_code}")
    except Exception as e:
        print(f"{e}: Error starting Synthea.")
        sys.exit(1)

    print("Connections check successful.")
    return True


def process_chain(guid, first_node, chain, file, file_type):
    """
    Given a chain, we iterate through the steps in it
    """
    for step_number, step in enumerate(chain):
        # First step is Synthea or File
        (error, file) = process_step(
            guid, first_node, step_number, step, chain, file, len(chain), file_type
        )
        if error:
            print(f"Error encountered processing step {step_number}, node {step}")
            break


def dfs(guid, first_node, counter, step, chain, chain_length, file, file_type):
    """
    Run a depth-first search to compute all possible chains
    """
    error = False
    if len(chain) > 0:
        tmp_chain = copy.deepcopy(chain)
        if len(tmp_chain) != chain_length:
            tmp_chain = tmp_chain + (chain_length - len(tmp_chain)) * [step]
        (error, file) = process_step(
            guid,
            first_node,
            counter - 1,
            step,
            tmp_chain,
            file,
            chain_length,
            file_type,
        )
    if counter > chain_length - 1:
        return
    if error:
        return
    for node in list(config.keys()):
        dfs(
            guid,
            first_node,
            counter + 1,
            node,
            chain + [node],
            chain_length,
            file,
            file_type,
        )


def process_step(
    guid, first_node, step_number, step, chain, file, chain_length, file_type
):
    """
    Process one entire step
    Checks if we got a patient id generated by ingesting a file. If not, we hit an error.
    """
    (patient_id, response_json_1, response_json_2) = client_map[step].step(
        step_number, file, file_type
    )
    if patient_id is None:
        print(
            f"Chain terminated at step {step_number} {step} {response_json_1} {response_json_2}"
        )
        """
        Connection to this current node failed.
        So either this node could not ingest the file or could not export
        Either way, we create an edge to this node
        and another edge from this node to terminated
        Why: a JSON blob is returned when the node cannot ingest it
        This way we also know clearly where it failed
        """
        if step_number == 0:
            db.create_edge(guid, first_node, step, file)
            db.create_edge(guid, step, "termination", response_json_2)
        else:
            db.create_edge(guid, chain[step_number - 1], step, file)
            db.create_edge(guid, step, "termination", response_json_2)

        return (True, response_json_2)
        # We must not be terminating the entire run, just what cannot be reached after
    if step_number == chain_length - 1 and step_number == 0:
        # Last element
        db.create_edge(guid, first_node, step, file)
        db.create_edge(guid, step, "end", response_json_2)
    elif step_number == 0:
        """
        If its the first hop then we need to read the first_node field
        """
        db.create_edge(guid, first_node, step, file)
    elif step_number == chain_length - 1:
        # Last element
        db.create_edge(guid, chain[step_number - 1], step, file)
        db.create_edge(guid, step, "end", response_json_2)

    else:
        db.create_edge(guid, chain[step_number - 1], step, file)

    return (False, response_json_2)


chain_config = OptionGroup(
    "Configure all chains", help="How to configure all enumerated chains"
)


@click.command()
@add_chain_options
def cli_options(chain_length, file, generate, chain, all_chains, file_type, diff_type):
    telephone_function(
        chain_length, file, generate, chain, all_chains, file_type, diff_type
    )


def telephone_function(
    chain_length, file, generate, chain, all_chains, file_type, diff_type
):
    """Command line options for the telephone.py script
    Vista takes a different format (Bundle Resource) as input, whereas others require a patient
    """
    check_connection(chain)  # Make sure all the images are up
    validate_options(file_type, chain, all_chains)
    first_node = "file"  # By default assume that we are reading from a CLI file
    guid = str(uuid.uuid4())

    # Create nodes in the neo4j database for all the servers we use
    # It won't create duplicate nodes for the servers
    # We add additional nodes to denote the end of a chain and how many keys are present
    db.create_nodes(list(config.keys()) + ["synthea", "file", "end", "termination"])

    # Generate a new FHIR JSON file
    if file:
        if isinstance(file, str):
            # If file is a string path, open and read file
            with open(file, "r") as f:
                file = f.read()
        else:
            # If file is like a file object, read it
            file = file.read()

    if generate:
        first_node = "synthea"  # generated by Synthea, not a file read
        r = requests.get("http://localhost:9000/", timeout=100)
        file_type = "json"
        if r.status_code == 200:
            filename = r.json()["filename"]

            # Setting base path to make generated file readable from tests
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
            file = open(os.path.join(base_path, f"files/fhir/{filename}")).read()

            print(f"Successfully created file for {filename}")
        else:
            print("File creation failed from Synthea")
            sys.exit(1)

    if all_chains:
        # Traverse all the chains possible now
        dfs(guid, first_node, 0, "", [], chain_length, file, file_type)
    else:
        # all chains not specified, so we specified specific hops
        process_chain(guid, first_node, chain, file, file_type)
    return guid


if __name__ == "__main__":
    cli_options()
