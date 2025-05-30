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
import configparser
import requests
import json
import docker
import time

from cli_options import add_chain_options

from utils.fhir_utils import SERVER_NAME
import click
from click_option_group import OptionGroup

sys.path.append("./clients")
from blaze_client import BlazeClient
from hapi_client import HapiClient
from ibm_fhir_client import IBMFHIRClient
from vista_client import VistaClient
from iris_client import IrisClient


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
    "iris": (config["DEFAULT"]["iris"], config["DEFAULT"]["iris-target"]),
}

vista_client = VistaClient(config["vista"][0], config["vista"][1])
ibm_client = IBMFHIRClient(config["ibm"][0], config["ibm"][1])
hapi_client = HapiClient(config["hapi"][0], config["hapi"][1])
blaze_client = BlazeClient(config["blaze"][0], config["blaze"][1])
iris_client = IrisClient(config["iris"][0], config["iris"][1])

client_map = {
    "vista": vista_client,
    "ibm": ibm_client,
    "hapi": hapi_client,
    "blaze": blaze_client,
    "iris": iris_client,
}


def validate_options(file_type, chain, all_chains):
    """Validate the combination of options."""
    if file_type.lower() == "xml" and (
        all_chains or any(c in chain for c in ["vista"])
    ):
        raise click.BadParameter(
            "Combination not possible: --type xml with -c vista, or --all-chains."
        )


def restart_container(container_name):
    """Stop and then start a Docker container by name."""
    docker_client = docker.from_env()
    for container in docker_client.containers.list():
        if container_name.lower() in container.name.lower():
            print(f"Stopping container: {container.name}")
            container.stop()
            time.sleep(20)  # brief wait after stop

            print(f"Starting container: {container.name}")
            container.start()
            time.sleep(420)  # wait for full startup


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
        clients = [vista_client, ibm_client, hapi_client, blaze_client, iris_client]
        client_names = ["vista", "ibm", "hapi", "blaze", "iris"]

    for iterator, client in enumerate(map(lambda x: x.export_patients(), clients)):
        try:
            if not 200 <= client[0] < 300:
                print(client[1])
                print(
                    f"{client_names[iterator]} server not up. Restarting FHIR containers..."
                )

                # Restart FHIR containers
                docker_client = docker.from_env()
                print(docker_client)

                containers_to_restart = []

                # Determine containers to restart
                if "vista" in [name.lower() for name in client_names]:
                    containers_to_restart.extend(["vista", "vehu"])
                else:
                    containers_to_restart.extend(client_names)

                # Restart containers
                for cname in containers_to_restart:
                    restart_container(cname)

                # Retry checking connection up to 3 times
                retries = 3
                while retries > 0:
                    time.sleep(180)  # Wait 3 minutes before rechecking

                    client = clients[iterator].export_patients()

                    if 200 <= client[0] < 300:
                        print(f"{client_names[iterator]} server is back up!")
                        break

                    retries -= 1
                    print(
                        f"Retry {3 - retries}/3: {client_names[iterator]} server still not up. Restarting containers again."
                    )

                    # Restart containers again on retry
                    for cname in containers_to_restart:
                        restart_container(cname)

                if retries == 0:
                    print(f"{client_names[iterator]} server did not recover. Exiting.")
                    sys.exit(1)

        except Exception as e:
            print(f"{client_names[iterator]} exiting with error {e}")
            sys.exit(1)

    print("Connections check successful.")
    return True


def process_chain(guid, first_node, chain, file, file_type, name):
    """
    Given a chain, we iterate through the steps in it
    """
    for step_number, step in enumerate(chain):
        # First step is Synthea or File
        (error, server_response, pat_file) = process_step(
            guid, first_node, step_number, step, chain, file, len(chain), file_type, name
        )
        # response_file_name = (
        #     "output-test/" + chain[0] + "/" + chain[0] + "_" + name.split("/")[1]
        # )
        # with open(response_file_name, "w", encoding="utf-8") as f:
        #     json.dump(file, f, ensure_ascii=False, indent=4)
        if error:
            print("error")
            response_file_name = f"temp_error_{SERVER_NAME}.json"
            with open(response_file_name, "w", encoding="utf-8") as f:
                json.dump(server_response, f, ensure_ascii=False, indent=4)
            break
        else:
            print("success")
            response_file_name = f"temp_response_{SERVER_NAME}.json"
            with open(response_file_name, "w", encoding="utf-8") as f:
                json.dump(pat_file, f, ensure_ascii=False, indent=4)


def process_step(
    guid, first_node, step_number, step, chain, file, chain_length, file_type, name
):
    """
    Process one entire step
    Checks if we got a patient id generated by ingesting a file. If not, we hit an error.
    """
    (patient_id, response_json_1, response_json_2) = client_map[step].step(
        step_number, file, file_type, name
    )
    if patient_id is None:
        # print(
        #     f"Chain terminated at step {step_number} {step} {response_json_1} {response_json_2}"
        # )

        return (True, response_json_1, response_json_2)

    return (False, response_json_1, response_json_2)


chain_config = OptionGroup(
    "Configure all chains", help="How to configure all enumerated chains"
)


@click.command()
@add_chain_options
def cli_options(chain_length, file, generate, chain, all_chains, file_type, diff_type, code_tag):
    telephone_function(
        chain_length, file, generate, chain, all_chains, file_type, diff_type, code_tag
    )


def telephone_function(
    chain_length, file, generate, chain, all_chains, file_type, diff_type, code_tag
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
    # db.create_nodes(list(config.keys()) + ["synthea", "file", "end", "termination"])
    name = code_tag
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
        print("Generating a new file")
        # first_node = "synthea"  # generated by Synthea, not a file read
        # r = requests.get("http://localhost:9000/", timeout=100)
        # file_type = "json"
        # name = "syn-create"
        # if r.status_code == 200:
        #     filename = r.json()["filename"]

        #     # Setting base path to make generated file readable from tests
        #     base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
        #     file = open(os.path.join(base_path, f"files/fhir/{filename}")).read()

        #     print(f"Successfully created file for {filename}")
        # else:
        #     print("File creation failed from Synthea")
        #     sys.exit(1)

    # if all_chains:
    #     # Traverse all the chains possible now
    #     dfs(guid, first_node, 0, "", [], chain_length, file, file_type)
    else:
        # all chains not specified, so we specified specific hops
        process_chain(guid, first_node, chain, file, file_type, name)

    return guid


if __name__ == "__main__":
    cli_options()
