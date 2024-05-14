import click
from click_option_group import (
    optgroup,
    OptionGroup,
    RequiredMutuallyExclusiveOptionGroup,
)
from neo4j import GraphDatabase


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "fhir-garden")


def run_query(query, guid=None):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session(database="neo4j") as session:
            if guid:
                result = session.run(query, guid=guid)
            else:
                result = session.run(query)
            return [record["path"] for record in result]


def print_paths(paths):
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
    if compare:
        if guid:
            query = """
                MATCH path = (a:Server {name: 'synthea'})-[:LINK*]->(c:Server {name: 'end'})
                WHERE ALL(r IN relationships(path) WHERE r.guid = $guid)
                AND ALL(n IN nodes(path) WHERE SINGLE(x IN nodes(path) WHERE x = n))
                RETURN path
            """
            paths = run_query(query, guid=guid)
            print_paths(paths)
        elif all_paths:
            query = """
                MATCH path = (a:Server {name: 'synthea'})-[:LINK*]->(c:Server {name: 'end'})
                WHERE ALL(n IN nodes(path) WHERE SINGLE(x IN nodes(path) WHERE x = n))
                RETURN path
            """
            paths = run_query(query)
            print_paths(paths)
    else:
        click.echo("Comparison not enabled. Use --compare to enable.")


if __name__ == "__main__":
    db_query()
