"""
Module to abstract click command options
"""

import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

config = ["vista", "ibm", "blaze", "hapi"]


def add_diff_options(func):
    """Decorator to add chain options to a Click command."""

    @click.option(
        "--guid", type=str, required=True, default=None, help="GUID for specific chain."
    )
    @click.option(
        "--type",
        "file_type",
        type=str,
        required=True,
        default=None,
        help="Patient file type - json or xml",
    )
    @click.option(
        "--diff",
        "diff_type",
        type=str,
        required=True,
        default="full",
        help="Diff output type - summary or full",
    )
    @optgroup.group(
        "Either choose depth = 1 or choose all depths.",
        cls=RequiredMutuallyExclusiveOptionGroup,
        help="Group description",
    )
    @optgroup.option("--depth", type=int, default=0, help="For depth of 1.")
    @optgroup.option("--all-depths", "all_depths", is_flag=True, default=False)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def add_chain_options(func):
    """Decorator to add chain options to a Click command."""

    @click.option("--chain-length", "chain_length", default=3, type=int)
    @click.option(
        "--type",
        "file_type",
        type=str,
        default=None,
        help="Patient file type - json or xml",
    )
    @click.option(
        "--diff",
        "diff_type",
        type=str,
        required=False,
        default="full",
        help="Diff output type - summary or full",
    )
    @optgroup.group(
        "Either generate a file or provide a command-line argument",
        cls=RequiredMutuallyExclusiveOptionGroup,
        help="Group description",
    )
    @optgroup.option("--file", type=click.File("r"))
    @optgroup.option("--generate", "generate", is_flag=True, default=False)
    @optgroup.group(
        "Either use a chain or generate all chains",
        cls=RequiredMutuallyExclusiveOptionGroup,
        help="Group description",
    )
    @optgroup.option(
        "--chain",
        "-c",
        multiple=True,
        type=click.Choice(config),
    )
    @optgroup.option("--all-chains", "all_chains", is_flag=True, default=False)
    def wrapper(*args, **kwargs):
        if kwargs.get("generate"):
            kwargs["file_type"] = "json"  # Default file_type for generate
        elif kwargs.get("file") and not kwargs.get("file_type"):
            raise click.BadParameter("You must specify --type when using --file")
        return func(*args, **kwargs)

    return wrapper
