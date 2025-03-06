"""Find max depth for each Patient file"""

import json
import os
import csv
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio

from resource_type_paths import parse_fhir_spec_csv, list_files_in_folder

RESOURCES_FOLDER = "output/resource"
TYPES_FOLDER = "output/types"


def max_depth_traverse(data_to_parse, depth, spec_file, graph, chain_path):
    """Recursively traverse patient data and construct graph"""

    metadata = parse_fhir_spec_csv(spec_file)
    current_node = os.path.basename(spec_file).split(".")[0]
    max_depth = depth
    longest_chain = chain_path

    for key, details in metadata.items():
        if (
            "type" in details and details["type"][0].isupper()
        ):  # Check if type is a nested type
            nested_type = details["type"]

            if key in data_to_parse:  # Check if this field exists in the patient data
                value = data_to_parse[key]

                resource_nested_spec_file = os.path.join(
                    RESOURCES_FOLDER, f"{nested_type}.csv"
                )
                type_nested_spec_file = os.path.join(TYPES_FOLDER, f"{nested_type}.csv")
                nested_spec_file = (
                    resource_nested_spec_file
                    if os.path.exists(resource_nested_spec_file)
                    else type_nested_spec_file
                )

                if os.path.exists(nested_spec_file):
                    graph.add_edge(current_node, nested_type)
                    nested_chain = chain_path + [nested_type]
                    nested_depth = depth + 1

                    if isinstance(
                        value, list
                    ):  # If its a list, use for loop to traverse through each element
                        for list_element in value:
                            if isinstance(list_element, dict):
                                temp_depth, temp_chain = max_depth_traverse(
                                    list_element,
                                    nested_depth,
                                    nested_spec_file,
                                    graph,
                                    nested_chain,
                                )
                                if temp_depth > max_depth:
                                    max_depth = temp_depth
                                    longest_chain = temp_chain

                    elif isinstance(value, dict):
                        temp_depth, temp_chain = max_depth_traverse(
                            value, nested_depth, nested_spec_file, graph, nested_chain
                        )

                        if temp_depth > max_depth:
                            max_depth = temp_depth
                            longest_chain = temp_chain

    return max_depth, longest_chain


patient_data = {}

# Process all resource files
synthea_patient_files = list_files_in_folder("synthea_files")
for synthea_file in synthea_patient_files:
    temp_name = (synthea_file.split("/")[1]).split(".")[0]
    file_name = temp_name.split("_")[0] + "-" + temp_name.split("_")[1]
    print(f"Processing file: {file_name}")

    # Reading the patient file
    with open(synthea_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = nx.MultiDiGraph()
    max_depth_chains = {}

    # Set patient file as the root node
    current_node = (
        os.path.basename(synthea_file).split("_")[0]
        + "_"
        + os.path.basename(synthea_file).split("_")[1]
    )
    graph.add_node(current_node)
    chain_path = [current_node]

    max_depth_across = 0
    max_depth_chain_across = []

    # Start creating the graph
    for entry in data.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if not resource_type:  # Ensure resourceType exists
            continue

        resource_spec_file = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
        if os.path.exists(resource_spec_file):
            graph.add_edge(current_node, resource_type)
            nested_chain_path = chain_path + [resource_type]
            max_depth, longest_chain = max_depth_traverse(
                resource, 1, resource_spec_file, graph, nested_chain_path
            )
            max_depth_chains[resource_type] = (max_depth, longest_chain)

        if max_depth > max_depth_across:
            max_depth_across = max_depth
            max_depth_chain_across = longest_chain
    patient_data[file_name] = {
        "num_nodes": len(graph.nodes()),
        "num_edges": len(graph.edges()),
        "max_depth": max_depth_across,
        "max_depth_chain": max_depth_chain_across,
        "first_level_nodes": len(list(graph.successors(current_node))),
    }

with open("all_patient_files_data.json", "w", encoding="utf-8") as f:
    json.dump(patient_data, f, ensure_ascii=False, indent=4)
