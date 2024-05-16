"""
Compare input and output patient data files passing through different FHIR nodes
"""

import click
from click_option_group import (
    optgroup,
    RequiredMutuallyExclusiveOptionGroup,
)
from neo4j import GraphDatabase
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
                result = session.run(query, params=params)
                paths = [record["path"] for record in result]
                if not paths:
                    print("No paths found matching the criteria.")
                return paths
        except Exception as e:
            print(f"Error {e} verifying db connection")
        finally:
            driver.close()


def print_paths(paths):
    file_index = 1
    for path in paths:
        for relationship in path.relationships:
            json_data = json.dumps(dict(relationship))
            with open(f"{file_index}.json", "w") as file:
                file.write(json.loads(json_data)["json"])
            file_index += 1


@click.command()
@click.option("--compare", is_flag=True, help="Enable file comparison operations.")
@optgroup.group(
    "GUID Options",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Specify one GUID or select all paths.",
)
@optgroup.option("--guid", default=None, help="GUID for specific chain.")
@optgroup.option(
    "--all-guids", "all_guids", is_flag=True, help="Select all paths across all GUIDs."
)
@optgroup.group(
    "Depth Options",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Control the search depth.",
)
@optgroup.option("--depth", type=int, default=1, help="For depth of 1.")
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
                    MATCH path = (a:Server {name: 'synthea'})-[:LINK*1..1]->(b:Server)-[:LINK*1..1]->(c:Server {name: 'end'})
                    WHERE ALL(r IN relationships(path) WHERE r.guid = $guid)
                    RETURN path
                """
            elif all_depths:
                # Search for all paths, filtered by GUID
                query = """
                    MATCH path = (a:Server {name: 'synthea'})-[:LINK*]->(c:Server {name: 'end'})
                    WHERE ALL(r IN relationships(path) WHERE r.guid = $guid)
                    RETURN path
                """
        elif all_guids:
            params = None
            if depth == 1:
                # Search for paths with exactly one intermediate node
                query = """
                    MATCH path = (a:Server {name: 'synthea'})-[:LINK*1..1]->(b:Server)-[:LINK*1..1]->(c:Server {name: 'end'})
                    RETURN path
                """
            elif all_depths:
                # Search for all paths irrespective of depth
                query = """
                    MATCH path = (a:Server {name: 'synthea'})-[:LINK*]->(c:Server {name: 'end'})
                    RETURN path
                """
        else:
            print("Please specify a GUID option.")
            return

        paths = run_query(query, params)
        print_paths(paths)
    else:
        click.echo("Comparison not enabled. Use --compare to enable.")


if __name__ == "__main__":
    db_query()
