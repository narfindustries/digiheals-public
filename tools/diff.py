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


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "fhir-garden")


def run_query(query, params=None):
    """Connect to db and execute Cypher query"""
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        try:
            driver.verify_connectivity()
            print("Connection to db successful.")
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


def compare_function(json1, json2):
    """Compare two JSON objects and return their differences using DeepDiff."""
    diff = DeepDiff(json1, json2, ignore_order=True)
    if diff:
        return False, diff
    return True, "JSON FHIR data is identical."


def compare_paths(paths):
    """Create struct for all segments of a path and internally compare those segments."""
    for path in paths:
        # Dict to store json data by GUID. Each entry contains another dict with link number as key.
        json_data_map = {}
        link_number = 1

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

        for guid, links in json_data_map.items():
            # Sort link numbers for the sequence of chain to be maintained
            sorted_link_numbers = sorted(links.keys())

            # If sorted list contains only 0 or 1 entry, there is nothing for this to be compared with.
            if len(sorted_link_numbers) < 2:
                continue

            print(
                "Links:",
                [(guid, ln, links[ln][0], links[ln][1]) for ln in sorted_link_numbers],
            )

            # Compare json data between consecutive link numbers within same guid
            for i in range(len(sorted_link_numbers) - 1):
                current_link_number = sorted_link_numbers[i]
                next_link_number = sorted_link_numbers[i + 1]

                json1 = links[current_link_number][2]
                json2 = links[next_link_number][2]

                if json1 and json2:
                    match, result = compare_function(json1, json2)
                    print(
                        f"Comparing FHIR data between link: {current_link_number} and {next_link_number} for GUID {guid}:"
                    )
                    print(
                        f"Path Nodes: {links[current_link_number][0]} -> {links[current_link_number][1]} and {links[next_link_number][0]} -> {links[next_link_number][1]}"
                    )
                    if match:
                        print(result)
                    else:
                        print(f"Differences: {result}")
                else:
                    print(
                        f"Data missing for comparison between links: {current_link_number} and {next_link_number}."
                    )


@click.command()
@click.option("--compare", is_flag=True, help="Enable file comparison operations.")
@optgroup.group(
    "GUID Options",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Specify one GUID or select all paths.",
)
@optgroup.option("--guid", type=str, default=None, help="GUID for specific chain.")
@optgroup.option(
    "--all-guids", "all_guids", is_flag=True, help="Select all paths across all GUIDs."
)
@optgroup.group(
    "Depth Options",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Control the search depth.",
)
@optgroup.option("--depth", type=int, default=0, help="For depth of 1.")
@optgroup.option(
    "--all-depths", "all_depths", is_flag=True, help="Search across all depths."
)
def db_query(compare, guid, all_guids, depth, all_depths):
    """Command line options to run comparisons"""
    if compare:
        if guid:
            params = {"guid": guid}
            if depth == 1:
                # Search for paths with exactly one intermediate node, filtered by GUID
                query = """
                    MATCH path = (a:Server)-[:LINK*1..1]->(b:Server)-[:LINK*1..1]->(c:Server {name: 'end'})
                    WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                    RETURN path
                """
            elif all_depths:
                # Search for all paths, filtered by GUID
                query = """
                    MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                    WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                    RETURN path
                """
        elif all_guids:
            params = None
            if depth == 1:
                # Search for paths with exactly one intermediate node
                query = """
                    MATCH path = (a:Server)-[:LINK*1..1]->(b:Server)-[:LINK*1..1]->(c:Server {name: 'end'})
                    WHERE a.name IN ['synthea', 'file']
                    RETURN path
                """
            elif all_depths:
                # Search for all paths irrespective of depth
                query = """
                    MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                    WHERE a.name IN ['synthea', 'file']
                    RETURN path
                """
        else:
            print("Please specify a GUID option.")
            return
        paths = run_query(query, params)
        compare_paths(paths)
    else:
        click.echo("Comparison not enabled. Use --compare to enable.")


if __name__ == "__main__":
    db_query()
