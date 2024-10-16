"""
Script to telephone.py and diff.py
"""

import json
import os
import click

from defusedxml.ElementTree import fromstring, ParseError

from cli_options import add_chain_options
from telephone import telephone_function, validate_options
from diff import db_query


config = ["vista", "ibm", "blaze", "hapi"]


def validate_file_type(file_type, file):
    """Validate file and file_type"""
    content = file.read()
    file.seek(0)
    if file_type.lower() == "xml":
        try:
            fromstring(content)
            return True
        except ParseError:
            raise click.BadParameter("File is not XML")

    else:
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            raise click.BadParameter("File is not JSON")


@click.command()
@add_chain_options
def main(chain_length, file, generate, chain, all_chains, file_type, diff_type):
    """Construct cli command and sequentially run telephone.py and diff.py"""
    # Validate --generate and --file arguments
    if generate and file:
        raise click.UsageError("Cannot use both --generate and --file together.")
    if not generate and not file:
        raise click.UsageError("Choose either --generate or --file.")

    # Validate -c and --all-chains arguments
    if chain and all_chains:
        raise click.UsageError("Cannot use both --chain and --all-chains together.")
    if not chain and not all_chains:
        raise click.UsageError("Choose either --chain or --all-chains.")

    # Validate the user input options
    if file:
        validate_file_type(file_type, file)
    validate_options(file_type, chain, all_chains)

    if diff_type == "summary":
        # Validate openAI keys
        if not (
            "OPENAI_API_KEY" in os.environ
            and "ORGANIZATION_KEY" in os.environ
            and "PROJECT_KEY" in os.environ
        ):
            raise click.UsageError("OpenAI API keys not set.")

    # Run telephone.py with either --generate or --file
    guid = telephone_function(
        chain_length, file, generate, chain, all_chains, file_type, diff_type
    )
    all_depths = False
    depth = 0
    if chain:
        # If user specifies chain, set all_depths flag to true
        all_depths = True
    if all_chains:
        # Return results of depth = 1 only
        depth = 1
    db_query(guid, depth, all_depths, file_type, diff_type)


if __name__ == "__main__":
    main()
