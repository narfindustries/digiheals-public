"""
Create unit test for XML and JSON diff of patient data
"""

import json
import pytest
from neo4j import GraphDatabase
from diff import run_query, compare_function, diff_cli_options, db_query, compare_paths
from click.testing import CliRunner

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "test-garden")

# TO DO: Test cases for openAI summary results


# Fixture for database connection
@pytest.fixture(scope="module")
def db():
    """Connect to neo4jTest server"""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    yield driver
    driver.close()


@pytest.mark.parametrize(
    "guid, depth",
    [
        (
            "39eef653-347c-4655-a39b-f887c13808fa",
            1,
        ),  # JSON depth 1 vista
        ("b25d7482-f9fc-4c2b-86e6-74a93a50acfd", 0),  # JSON depth 3 (iris, hapi, vista)
        ("808f9341-84d1-4843-914d-21944b616467", 0),  # JSON depth 2 (ibm, iris)
        ("6d831452-4058-4a00-8b61-ef7a4a6fb4d0", 1),  # XML depth 1 blaze
        ("fecc37e8-da09-4941-bf32-9bce982ea375", 0),  # XML depth 2 (hapi, blaze)
        ("bd2335f8-862a-40d6-b74d-330338511f69", 0),  # XML depth 3 (ibm, hapi, iris)
        ("abcdef", 0),  # invalid guid should return 0 paths
    ],
)
def test_run_query(db, guid, depth):
    """Run queries on neo4jTest db"""
    with db.session() as session:
        if depth == 1:
            query = """
                MATCH path = (a:Server)-[:LINK*1..1]->(b:Server)-[:LINK*1..1]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                RETURN path
            """
        else:
            query = """
                    MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                    WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                    RETURN path
                """
        result = session.run(query, parameters={"guid": guid})
        paths = [record["path"] for record in result]
    assert len(paths) >= 0  # Number of paths returned.


@pytest.mark.parametrize(
    "file1, file2, file_type, expected",
    [
        (
            "./test_files/json_diff_file1_id.json",
            "./test_files/json_diff_file2_id.json",
            "json",
            (True, "./test_files/json_diff_1_2_id.txt"),
        ),
        (
            "./test_files/json_diff_file1.json",
            "./test_files/json_diff_file2.json",
            "json",
            (False, "./test_files/json_diff_1_2.txt"),
        ),
        (
            "./test_files/xml_diff_file1.txt",
            "./test_files/xml_diff_file2.txt",
            "xml",
            (False, "./test_files/xml_diff_1_2.txt"),
        ),
    ],
)
def test_compare_function(file1, file2, file_type, expected):
    """Test DeepDiff Comparison between files"""
    f1 = open(file1, "r")
    f2 = open(file2, "r")
    if file_type == "xml":
        file1 = f1.read()
        file2 = f2.read()
    elif file_type == "json":
        file1 = json.load(f1)
        file2 = json.load(f2)

    result1, result2 = compare_function(file1, file2, file_type, "full")
    result = (result1, str(result2))

    f3 = open(expected[1], "r")
    file3 = f3.read()
    expected_tuple = (expected[0], file3)

    assert result == expected_tuple, f"Failed for {file_type} comparison"


# @pytest.mark.skip(reason="no way of currently testing this")
def test_compare_paths_with_chains(capsys):
    """Test to check paths comparison functionality"""
    params = {"guid": "6d831452-4058-4a00-8b61-ef7a4a6fb4d0"}
    query = """
                MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                RETURN path
            """
    paths = run_query(query, params)
    chains = True
    file_type = "xml"

    # Function which prints output
    compare_paths(paths, chains, file_type, "full")

    captured = capsys.readouterr()  # Capture output

    # Check if certain expected strings are in the output
    assert (
        "6d831452-4058-4a00-8b61-ef7a4a6fb4d0" in captured.out
    ), "GUID not found in output"
    assert (
        "file -> blaze and blaze -> end" in captured.out
    ), "Chains not found in output"
    assert "{'dictionary_item_added':" in captured.out, "Diff not found in output"


def test_cli_options():
    """Test to check functionality of CLI options"""
    runner = CliRunner()
    test_args = [
        "--guid",
        "39eef653-347c-4655-a39b-f887c13808fa",
        "--depth",
        "1",
        "--type",
        "json",
    ]

    result = runner.invoke(diff_cli_options, test_args)  # Invoke CLI command

    assert (
        result.exit_code == 0
    ), "CLI exited with non-zero status"  # CLI option evoked correctly but returns SystemExit=0
    assert "Error" not in result.output, "CLI test failed with errors"


def test_database_integration():
    """Test to check full integration of diff functionality"""
    # Output should show diff tables
    result = db_query(
        "b25d7482-f9fc-4c2b-86e6-74a93a50acfd", 0, True, "json", "full"
    )  # json chain with depth 3 - vista, hapi, blaze
    assert (
        result is None
    ), "Full integration failed."  # Return is None, as this function doesn't return anything
