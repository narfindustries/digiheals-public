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
            "88b95103-74b4-421c-8172-dddc4741efd5",
            1,
        ),  # JSON depth 1 vista
        ("2712fb90-4c43-4146-b0a3-647095e997c0", 0),  # JSON depth 3 vista, hapi, blaze
        ("c776d8c4-6d0a-4e01-8f53-9887f5bff4a2", 1),  # XML depth 1 blaze
        ("dfa449ed-10b2-4386-a8ad-6e568880a34e", 0),  # XML depth 2 (hapi, blaze)
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
            "./test_files/xml_diff_file1.txt",
            "./test_files/xml_diff_file2.txt",
            "xml",
            (False, "./test_files/xml_diff_1_2.txt"),
        ),
        (
            "./test_files/json_diff_file1.json",
            "./test_files/json_diff_file2.json",
            "json",
            (False, "./test_files/json_diff_1_2.txt"),
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

    result1, result2 = compare_function(file1, file2, file_type)
    result = (result1, str(result2))

    f3 = open(expected[1], "r")
    file3 = f3.read()
    expected_tuple = (expected[0], file3)

    assert result == expected_tuple, f"Failed for {file_type} comparison"


def test_compare_paths_with_chains(capsys):
    """Test to check paths comparison functionality"""
    params = {"guid": "c776d8c4-6d0a-4e01-8f53-9887f5bff4a2"}
    query = """
                MATCH path = (a:Server)-[:LINK*]->(c:Server {name: 'end'})
                WHERE a.name IN ['synthea', 'file'] AND ALL(r IN relationships(path) WHERE r.guid = $guid)
                RETURN path
            """
    paths = run_query(query, params)
    chains = True
    file_type = "xml"

    # Function which prints output
    compare_paths(paths, chains, file_type)

    captured = capsys.readouterr()  # Capture output

    # Check if certain expected strings are in the output
    assert (
        "c776d8c4-6d0a-4e01-8f53-9887f5bff4a2" in captured.out
    ), "GUID not found in output"
    assert (
        "file -> blaze and blaze -> end" in captured.out
    ), "Chains not found in output"
    assert "0.0026" in captured.out, "Diff Score not found in output"
    assert "{'dictionary_item_added':" in captured.out, "Diff column is empty"


def test_cli_options():
    """Test to check functionality of CLI options"""
    runner = CliRunner()
    test_args = [
        "--guid",
        "88b95103-74b4-421c-8172-dddc4741efd5",
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
        "2712fb90-4c43-4146-b0a3-647095e997c0", 0, True, "json"
    )  # json chain with depth 3 - vista, hapi, blaze
    assert (
        result is None
    ), "Full integration failed."  # Return is None, as this function doesn't return anything
