Game of Telephone Design Document
-------------

## Command-line tool usage

The file `tools/telephone.py` contains the tooling to run the Game of Telephone.

- `--generate` (no arguments) to generate a file via Synthea. Or `--file FILENAME` to provide a file as a command-line argument.
- `-c HOP1 -c HOP2 -c HOP3` to run a file through HOP1, HOP2, and HOP3. Such a series generates at most 4 edges: (1) into HOP1, (2) HOP1 to HOP2, (3) HOP2 to HOP3, and (4) HOP3 to _end_. In case of an error in any particular node, an edge is created from HOPn to _termination_.
- `--all-chains --chain-length N` allows you to generate all chains instead of specifying one specific chain. 

## Visualization

Open `localhost:7474` for Neo4J. It uses the username and password: `neo4j/fhir-garden`.

```
match n return n
```

The above is a simple command to get you started and get all the nodes and edges in the Neo4J database.
