"""
Script to telephone.py and diff.py
"""

import subprocess
import re
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

from cli_options import add_chain_options

config = ["vista", "ibm", "blaze", "hapi"]


def run_command(command):
    """Run command and return output."""
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode != 0:
        print(f"Error running {command}: {result.stderr}")
        return None
    return result.stdout.strip()


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
    if generate:
        telephone_cli_command = (
            f"python telephone.py --generate {chain_args} --chain-length {chain_length}"
        )
    else:
        telephone_cli_command = f"python telephone.py --file {file.name} {chain_args} --chain-length {chain_length}"

    telephone_output = run_command(telephone_cli_command)
    if telephone_output:
        # Get GUID from the output using regex
        guid_match = re.search(r"\b([a-f0-9-]{36})\b", telephone_output)
        if guid_match:
            guid = guid_match.group(1)
            print(f"GUID: {guid}")

            # Construct diff.py cli command with GUID and depth options
            if depth:
                depth_arg = f"--depth {depth}"
            elif all_depths:
                depth_arg = "--all-depths"

            diff_cli_command = f"python diff.py --compare --guid {guid} {depth_arg}"
            diff_output = run_command(diff_cli_command)
            if diff_output:
                print(f"diff.py output:\n{diff_output}")
        else:
            print("GUID not found in telephone.py output.")
    else:
        print("Error running telephone.py.")


if __name__ == "__main__":
    main()
