"""
Create unit tests for Game Of Telephone
"""

import sys
import os
import pytest
from neo4j import GraphDatabase

# Adding path to clients directory to sys.path (err - clients not reachable from tests through telephone.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../clients")))
from telephone import telephone_function

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "test-garden")


# Fixture for database connection
@pytest.fixture(scope="module")
def neo4j_test_db():
    """Connect to neo4jTest server"""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        yield driver
    finally:
        driver.close()


@pytest.mark.parametrize(
    "chain_length, file, generate, chain, all_chains, file_type",
    [
        (2, None, True, ["hapi", "blaze"], False, "json"),
        (1, None, True, None, True, "json"),
        (
            1,
            "test_files/Elaina826_Dayna943_Marvin195_b25b43b3-3284-0867-dfdb-f8f9a32fbc91.xml",
            False,
            ["hapi"],
            False,
            "xml",
        ),
    ],
)
def test_chain_creation_and_cleanup(
    neo4j_test_db, chain_length, file, generate, chain, all_chains, file_type
):
    """Run telephone chain and test if edges are created"""

    guid = telephone_function(
        chain_length, file, generate, chain, all_chains, file_type
    )

    # Check if all nodes exist
    nodes = get_all_nodes(neo4j_test_db)
    assert len(nodes) == 8, "Missing few nodes"

    # Check if edges for this guid exist
    edges = get_edges_by_guid(neo4j_test_db, guid)
    assert len(edges) > 0, "No edges created for guid"

    # Clean up database by removing edges with this guid
    remove_edges_by_guid(neo4j_test_db, guid)
    edges_after_cleanup = get_edges_by_guid(neo4j_test_db, guid)
    assert len(edges_after_cleanup) == 0, "Edges not cleaned up after test"


def get_all_nodes(neo4j_test_db):
    """Query to get all nodes in the db"""
    with neo4j_test_db.session() as session:
        query = """MATCH (n) RETURN n.name"""
        result = session.run(query)
        return [record for record in result]


def get_edges_by_guid(neo4j_test_db, guid):
    """Query to get edges with a guid from the db"""
    with neo4j_test_db.session() as session:
        query = """MATCH (n1)-[p:LINK]->(n2)
            WHERE p.guid = $guid
            RETURN n1.name, p.guid, n2.name"""
        result = session.run(query, parameters={"guid": guid})
        return [record for record in result]


def remove_edges_by_guid(neo4j_test_db, guid):
    """Query to delete the edges with this guid from db created for this test"""
    with neo4j_test_db.session() as session:
        query = """MATCH (n1)-[r:LINK {guid: $guid}]->(n2)
            DELETE r"""
        session.run(query, parameters={"guid": guid})
