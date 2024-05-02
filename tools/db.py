#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a client for the Neo4J server
TODO: Functions in this file will throw errors/Exceptions.
"""

from neo4j import GraphDatabase
import json

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "fhir-garden")


def __create_servers(tx, name):
    """Create new Server node with given name, if not exists already"""
    result = tx.run(
        """
        MERGE (p:Server {name: $name})
        RETURN p.name AS name
        """,
        name=name,
    )
    return result


def create_nodes(nodes: list[str]):
    """
    Create nodes for various Servers and other metadata
    NOTE: Functions in this file will throw errors/Exceptions.
    Especially when the connection to Neo4J fails
    """
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session(database="neo4j") as session:
            for name in nodes:
                return_id = session.execute_write(__create_servers, name)
                print(f"{name} {return_id}")


def __create_edges(tx, guid, node1, node2, json_string):
    """Create new Edges"""
    result = tx.run(
        """
        MATCH (n1:Server {name: $node1}), (n2:Server {name: $node2})
        CREATE (n1)-[p:LINK {guid: $guid, json: $json_string}]->(n2)
        RETURN p.guid AS guid
        """,
        node1=node1,
        node2=node2,
        guid=guid,
        json_string=json.dumps(json_string),
    )
    return result


def create_edge(guid: str, node1: str, node2: str, json_string):
    """
    Create nodes for various Servers and other metadata
    Especially when the connection to Neo4J fails
    """
    print(f"{guid} {node1} {node2}")
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session(database="neo4j") as session:
            return_id = session.execute_write(
                __create_edges, guid, node1, node2, json_string
            )
            print(f"{guid} {return_id}")
