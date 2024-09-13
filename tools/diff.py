"""
Compare input and output patient data files passing through different FHIR nodes
"""

import json
import re
import textwrap
import os

import click
import xmltodict
from defusedxml.ElementTree import fromstring, ParseError
from tabulate import tabulate
from neo4j import GraphDatabase
from deepdiff import DeepDiff

from cli_options import add_diff_options

neo4j_env = os.getenv("COMPOSE_PROFILES", "neo4jDev")

if neo4j_env == "neo4jDev":
    URI = "neo4j://localhost:7687"
    AUTH = ("neo4j", "fhir-garden")
elif neo4j_env == "neo4jTest":
    URI = "neo4j://localhost:7688"
    AUTH = ("neo4j", "test-garden")


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


def clean_string_from_file(file):
    """Remove leading and trailing " from string, to avoid XML parsing errors"""
    if file.startswith('"') and file.endswith('"'):
        file = file[1:-1]
    return file


def compare_function(file1, file2, file_type):
    """Compare two objects and return their differences using DeepDiff"""
    if file_type.lower() == "xml":
        file1 = xmltodict.parse(clean_string_from_file(file1))
        file2 = xmltodict.parse(clean_string_from_file(file2))
    diff = DeepDiff(file1, file2, ignore_order=False, get_deep_distance=True)
    if diff:
        return False, diff

    return True, f"{file_type} FHIR data is identical."


def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width))


def is_increasing_consecutive(numbers):
    """Check if id list has all increasing numbers in consecutive order"""
    for i in range(len(numbers) - 1):
        if numbers[i] + 1 != numbers[i + 1]:
            return False
    return True


def xml_parse(xml_content):
    """Clean XML by replacing escaped newline characters with actual newlines"""
    corrected_xml = re.sub(
        r"\\'", "'", re.sub(r'\\"', '"', re.sub(r"\\n", "\n", xml_content))
    )
    return corrected_xml


def check_file_type(file, file_type):
    """Check file and file_type"""
    content = file.read()
    file.seek(0)
    if file_type.lower() == "xml":
        try:
            fromstring(content)
            return True
        except ParseError:
            raise click.BadParameter("File is not XML. Enter correct file type.")
    else:
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            raise click.BadParameter("File is not JSON. Enter correct file type.")


def check_json(file):
    """Check if the string starts with '{' or '['"""
    clean_file = clean_string_from_file(file)
    return clean_file.strip().startswith("{") or clean_file.strip().startswith("[")


def check_xml(file):
    """Check if the string starts with '<'"""
    clean_file = clean_string_from_file(file)
    return clean_file.strip().startswith("<")


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
            chain_order = False if relationship_ids[0] in edge_list else True

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

                    file1 = links[current_link_number][2]
                    file2 = links[next_link_number][2]

                    # Validating file with user input file_type
                    if (
                        check_json(file1)
                        and check_json(file2)
                        and file_type.lower() == "json"
                    ):
                        parse = json.loads
                    elif (
                        check_xml(file1)
                        and check_xml(file2)
                        and file_type.lower() == "xml"
                    ):
                        parse = xml_parse
                    else:
                        raise click.BadParameter("Re-check file type.")

                    file1 = parse(file1)
                    file2 = parse(file2)

                    if file1 and file2:
                        if (
                            links[current_link_number][0] == "synthea"
                            or links[current_link_number][0] == "file"
                        ):
                            if file_type.lower() == "json":
                                try:
                                    file1 = json.loads(
                                        file1
                                    )  # Need to load json twice as the data contains escaped spaces in string format
                                except json.JSONDecodeError as e:
                                    # print("Chain created, but input JSON is invalid:", e)
                                    file1 = None
                                    """Here, we say that the input file to a server is invalid, but then how did the server import it?
                                    We skip the compare path function and directly print an invalid message to the table.
                                    """
                                    pass

                            else:
                                file1 = clean_string_from_file(file1)
                                file2 = clean_string_from_file(file2)

                        if file1 is not None:
                            match, result = compare_function(file1, file2, file_type)
                            diff_score = (
                                0 if match else round(result["deep_distance"], 4)
                            )

                        else:
                            match = False
                            result = (
                                f"Malformed {file_type} input. Cannot perform Diff."
                            )
                            diff_score = "-"

                        chain_links = f"{links[current_link_number][0]} -> {links[current_link_number][1]} and {links[next_link_number][0]} -> {links[next_link_number][1]}"

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

                # print("\n")

        else:
            pass


@click.command()
@add_diff_options
def diff_cli_options(guid, depth, all_depths, file_type):
    db_query(guid, depth, all_depths, file_type)


def db_query(guid, depth, all_depths, file_type):
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
            # TBD: --all-depths query takes too long to process, when diff.py is run in isolation with --all-chains generated guid
            query = """
                MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                RETURN path
            """
            chains = True  # Set flag to show that chain sequence is defined by user
        else:
            print("Choose depth = 1 or all depths.")
            return
    else:
        print("Please specify a GUID option.")
        return
    paths = run_query(query, params)
    compare_paths(paths, chains, file_type)


if __name__ == "__main__":
    diff_cli_options()
