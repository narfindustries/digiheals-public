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


def run_query(query, guid=None):
    """Connect to db and execute Cypher query"""
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        try:
            driver.verify_connectivity()
            print("Connection to db successful.")
            with driver.session(database="neo4j") as session:
                if guid:
                    result = session.run(query, guid=guid)
                else:
                    result = session.run(query)
                return [record["path"] for record in result]
        except Exception as e:
            print(f"Error {e} verifying db connection")
        finally:
            driver.close()


def print_paths(paths):
    """Temporarily printing the paths for each chain"""
    for path in paths:
        for relationship in path.relationships:
            print(
                f"Relationship: {relationship.element_id}, Type: {relationship.type}, Start-Node: {relationship.start_node}, End-Node: {relationship.end_node}, Properties: {dict(relationship)}"
            )


@click.command()
@click.option("--compare", is_flag=True, help="Enable file comparison operations.")
@optgroup.group(
    "GUID Options",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Specify one GUID or select all paths.",
)
@optgroup.option("--guid", default=None, help="GUID for specific chain.")
@optgroup.option("--all-paths", is_flag=True, help="Select all paths across all GUIDs.")
def db_query(compare, guid, all_paths):
    """Command line options to run comparisons"""
    if compare:
        if guid:
            # User specified guid
            query = """
                MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                AND ALL(n IN nodes(path) WHERE SINGLE(x IN nodes(path) WHERE x = n))
                RETURN path
            """
            paths = run_query(query, guid=guid)
            print_paths(paths)
        elif all_paths:
            # For all chains from synthea/file to end
            query = """
                MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(n IN nodes(path) WHERE size([x IN nodes(path) WHERE x = n]) = 1)
                RETURN path
            """
            paths = run_query(query)
            print_paths(paths)
    else:
        click.echo("Comparison not enabled. Use --compare to enable.")


if __name__ == "__main__":
    db_query()
