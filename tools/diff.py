"""
Compare input and output patient data files passing through different FHIR nodes
"""

import click
from click_option_group import (
    optgroup,
    RequiredMutuallyExclusiveOptionGroup,
)
from neo4j import GraphDatabase
from deepdiff import DeepDiff
import json
from tabulate import tabulate
import textwrap
import re
import xmltodict
import lxml.etree as ET

from cli_options import add_diff_options

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "fhir-garden")


def run_query(query, params=None):
    """Connect to db and execute Cypher query"""
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        try:
            driver.verify_connectivity()
            # print("Connection to db successful.")
            with driver.session(database="neo4j") as session:
                result = session.run(query, parameters=params)
                paths = [record["path"] for record in result]
                if not paths:
                    print("No paths found matching the criteria.")
                return paths
        except Exception as e:
            print(f"Error {e} verifying db connection")
        finally:
            driver.close()


def compare_function(json1, json2, file_type):
    """Compare two JSON objects and return their differences using DeepDiff."""
    if file_type == "xml":
        if json1.startswith('"') and json1.endswith('"'):
            json1 = json1[1:-1]
        if json2.startswith('"') and json2.endswith('"'):
            json2 = json2[1:-1]
        json1 = xmltodict.parse(json1)
        json2 = xmltodict.parse(json2)
    diff = DeepDiff(json1, json2, ignore_order=True, get_deep_distance=True)
    if diff:
        return False, diff
    return True, f"{file_type} FHIR data is identical."


def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width))


def is_increasing_consecutive(numbers):
    """Check if id list has all increasing numbers in consecutive order."""
    for i in range(len(numbers) - 1):
        if numbers[i] + 1 != numbers[i + 1]:
            return False
    return True

def xml_parse(xml_content):
    # Replace escaped newline characters with actual newlines
    corrected_xml = re.sub(r'\\n', '\n', xml_content)
    corrected_xml = re.sub(r'\\"', '"', corrected_xml)
    corrected_xml = re.sub(r"\\'", "'", corrected_xml)

    return corrected_xml

def compare_paths(paths, chains, file_type):
    """Create struct for all segments of a path and internally compare those segments."""
    edge_list = []
    for path in paths:
        # Dict to store json data by GUID. Each entry contains another dict with link number as key.
        json_data_map = {}
        link_number = 1

        # Get path ids
        relationship_ids = [relationship.id for relationship in path.relationships]
        if chains:
            chain_order = is_increasing_consecutive(relationship_ids)
        else:
            if relationship_ids[0] in edge_list:
                chain_order = False
                break
            else:
                chain_order = True

        if chain_order:
            # Each segment of the path will have relationships
            for relationship in path.relationships:
                guid = relationship.get("guid", None)
                json_data = relationship.get("json", None)
                start_node_name = relationship.start_node.get("name", None)
                end_node_name = relationship.end_node.get("name", None)

                if guid not in json_data_map:
                    json_data_map[guid] = {}

                # Store data by link number in sub-struct for corresponding GUID
                json_data_map[guid][link_number] = (
                    start_node_name,
                    end_node_name,
                    json_data,
                )
                link_number += 1
                edge_list.append(
                    relationship_ids[0]
                )  # Assumption that only 1 unique edge exists from node a to node b for a given GUID

            for guid, links in json_data_map.items():
                # Sort link numbers for the sequence of chain to be maintained
                sorted_link_numbers = sorted(links.keys())

                # If sorted list contains only 0 or 1 entry, there is nothing for this to be compared with.
                if len(sorted_link_numbers) < 2:
                    continue

                # Compare json data between consecutive link numbers within same guid
                table_data = []
                for i in range(len(sorted_link_numbers) - 1):
                    current_link_number = sorted_link_numbers[i]
                    next_link_number = sorted_link_numbers[i + 1]
                    print("EEEEEEEEEEE", i)

                    if file_type == "json":
                        json1 = json.loads(links[current_link_number][2])
                        json2 = json.loads(links[next_link_number][2])
                    
                    else:
                        json1 = xml_parse(links[current_link_number][2])
                        json2 = xml_parse(links[next_link_number][2])                       

                    if json1 and json2:
                        if (
                            links[current_link_number][0] == "synthea"
                            or links[current_link_number][0] == "file"
                        ):
                            if file_type == "json":
                                syn_file = json.loads(json1)
                                # If resourceType in file is a Bundle, extract only Patient resourceType for comparison
                                if syn_file["resourceType"] == "Bundle":
                                    for entries in syn_file["entry"]:
                                        # Only one Patient resourceType exists
                                        if entries["resource"]["resourceType"] == "Patient":
                                            json1 = entries["resource"]
                            else:
                                
                                if json1.startswith('"') and json1.endswith('"'):
                                    json1 = json1[1:-1]
                                if json2.startswith('"') and json2.endswith('"'):
                                    json2 = json2[1:-1]
                                
                                tree = ET.ElementTree(ET.fromstring(json1))
                                root = tree.getroot()
                                ns = {"fhir": "http://hl7.org/fhir"}  # Define namespace
                                # Traverse XML tree to find Patient resource
                                for entry in root.findall("fhir:entry", ns):
                                    resource = entry.find("fhir:resource", ns)
                                    if resource is not None:
                                        patient = resource.find("fhir:Patient", ns)
                                        if patient is not None:
                                            json1 = ET.tostring(patient, encoding="unicode")
                        
                        match, result = compare_function(json1, json2, file_type)
                        chain_links = f"{links[current_link_number][0]} -> {links[current_link_number][1]} and {links[next_link_number][0]} -> {links[next_link_number][1]}"
                        diff_score = 0 if match else round(result["deep_distance"], 4)

                        # Wrap text for columns
                        wrapped_guid = wrap_text(guid, 40)
                        wrapped_chain_links = wrap_text(chain_links, 40)
                        wrapped_diff_score = wrap_text(str(diff_score), 20)
                        wrapped_diff = wrap_text(str(result), 60)

                        table_data.append(
                            [
                                wrapped_guid,
                                wrapped_chain_links,
                                wrapped_diff_score,
                                wrapped_diff,
                            ]
                        )
                        table_data.append(["" * 40, "-" * 40, "-" * 20, "-" * 60])

                if table_data:
                    # Remove the last separator row
                    table_data.pop()

                    # Merge GUID column for consecutive rows with the same GUID
                    current_guid = None
                    for row in table_data:
                        if row[1] == "-" * 40 or row[0] == current_guid:
                            row[0] = ""
                        else:
                            current_guid = row[0]

                    print(
                        tabulate(
                            table_data,
                            headers=["GUID", "Chain Links", "Diff Score", "Diff"],
                            tablefmt="pretty",
                        )
                    )

                print("\n")

        else:
            print("\n")


@click.command()
@add_diff_options
def diff_cli_options(guid, depth, all_depths):
    db_query(guid, depth, all_depths)


def db_query(guid, depth, all_depths, file_type="json"):
    """Command line options to run comparisons"""

    if guid:
        params = {"guid": guid}
        if depth == 1:
            # Search for paths with exactly one intermediate node, filtered by GUID
            query = """
                MATCH path = (a:Server)-[:LINK*1..1]->(b:Server)-[:LINK*1..1]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                RETURN path
            """
            chains = False  # Set flag where depth search is hardcoded to 1. TO DO: Change logic to work for depth > 1
        elif all_depths:
            # Search for all paths, filtered by GUID
            query = """
                MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                RETURN path
            """
            chains = True  # Set flag to show that chain sequence is defined by user
        else:
            print("Depth not valid.")
            return
    else:
        print("Please specify a GUID option.")
        return
    paths = run_query(query, params)
    compare_paths(paths, chains, file_type)


if __name__ == "__main__":
    diff_cli_options()
