"""
Script to telephone.py and diff.py
"""

import subprocess
import re
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

from cli_options import add_chain_options

from telephone import telephone_function
from diff import db_query

config = ["vista", "ibm", "blaze", "hapi"]


@click.command()
@optgroup.group(
    "Depth Options",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Control the search depth.",
)
@optgroup.option("--depth", type=int, default=0, help="For depth of 1.")
@optgroup.option(
    "--all-depths", "all_depths", is_flag=True, help="Search across all depths."
)
@add_chain_options
def main(chain_length, file, generate, chain, all_chains, depth, all_depths):
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

    # Validate --depth and --all_depths arguments
    if depth and all_depths:
        raise click.UsageError(
            "Cannot use both --depth <val> and --all_depths together."
        )
    if not depth and not all_depths:
        raise click.UsageError("Choose either --depth <val> and --all_depths.")

    # Construct user input chain arguments
    if chain:
        chain_args = " ".join([f"-c {ch}" for ch in chain])
    else:
        chain_args = "--all-chains"

    # Run telephone.py with either --generate or --file
    guid = telephone_function(chain_length, file, generate, chain, all_chains)
    db_query(True, guid, None, depth, all_depths)


if __name__ == "__main__":
    main()
