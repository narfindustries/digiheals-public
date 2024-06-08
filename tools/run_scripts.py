"""
Script to telephone.py and diff.py
"""

import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

from cli_options import add_chain_options

from telephone import telephone_function
from diff import db_query

config = ["vista", "ibm", "blaze", "hapi"]


@click.command()
@add_chain_options
def main(chain_length, file, generate, chain, all_chains):
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

    # Run telephone.py with either --generate or --file
    guid = telephone_function(chain_length, file, generate, chain, all_chains)
    all_depths = False
    depth = 0
    if chain:
        # If user specifies chain, set all_depths flag to true
        all_depths = True
    if all_chains:
        # Return results of depth = 1 only
        depth = 1
    db_query(guid, depth, all_depths)


if __name__ == "__main__":
    main()
