#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Skeleton for the Telephone.py script to go through multiple targets
"""
import click
from click_option_group import (
    optgroup,
    OptionGroup,
    RequiredMutuallyExclusiveOptionGroup,
)
import sys
from pathlib import Path

sys.path.append("./clients")

from fuzz_client import FuzzClient
from synthea_client import SyntheaClient


class FuzzInputFilePath(click.Path):
    """ensure file lives in fuzzable path under files/fhir/"""

    name = "file"

    def __init__(self):
        super().__init__(dir_okay=False, exists=True, resolve_path=True, path_type=Path)

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        if (
            value.parent == None
            or value.parent.parent == None
            or value.parent.name != "fhir"
            or value.parent.parent.name != "files"
        ):
            self.fail(
                f"{value} must have parent directory of 'files/fhir/'", param, ctx
            )
        return value.name


def fuzz(client, filename, count, no_wait):
    res, data = client.fuzz(filename, count)
    rlts = data.get("results", [])

    if res != 200 or not rlts:
        print(
            f"Failed to fuzz file {filename}. ",
            "Can only fuzz generated files or files in files/fhir subdirectory",
        )
        sys.exit(1)
    if not no_wait:
        # wait for fuzz to finish before reading file
        client.wait_until_done(filename)
    files = [f"../files/fuzzed/{r['output_name']}" for r in rlts]
    for f in files:
        # print names of created fuzzed files
        print(f)
    return files


@click.command()
@optgroup.group(
    "Either generate a file or provide a command-line argument",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Group description",
)
@optgroup.option(
    "--file",
    type=FuzzInputFilePath(),
    help="path to file to fuzz. Must be in ../files/fhir subdirectory",
)
@optgroup.option(
    "--generate",
    "generate",
    is_flag=True,
    default=False,
    help="If true, generates file to fuzz",
)
@optgroup.option(
    "--is-fuzzing",
    is_flag=True,
    default=False,
    help="Check if fuzzing jobs are still pending",
)
@click.option(
    "--url",
    type=str,
    default="http://localhost:9000",
    help="Url for synthea/fuzzing server",
)
@click.option(
    "-c",
    "--count",
    type=click.IntRange(min=1),
    default=1,
    help="number of times to fuzz file",
)
@click.option("--no-wait", is_flag=True, help="Don't wait for fuzzing to finish")
def cli_options(url, count, file, generate, is_fuzzing, no_wait):
    client = FuzzClient(url)
    if is_fuzzing:
        print(client.fuzz_terminated(None))
        sys.exit(0)
    if generate:
        sclient = SyntheaClient(url)
        (res, file) = sclient.generate()
    fuzz(client, file, count, no_wait)


if __name__ == "__main__":
    cli_options()
