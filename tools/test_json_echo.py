#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""A python script for testing json echo servers in bulk and
analyzing the results

"""

import click
from clients.echo_clients import EchoClient, EHRMapping
from pathlib import Path
from datetime import datetime
import os
import sys
import shutil
import logging
import deepdiff
import pprint
from utils import parser
import json

logger = logging.getLogger(__name__)
logging.basicConfig()



class ResultEncoder(json.JSONEncoder):
    """ Json serializer for deepdiff results"""
    def default(self, o):
        if isinstance(o, bytes):
            return o.decode('utf-8', errors="replace")
        elif isinstance(o, parser.JSONNode):
            return {"type": str(o.type), "value": str(o.value)}
        elif isinstance(o, type):
            return str(o)
        return super().default(o)


class OutputTree():
    """Class for traversing the input directory for json files and
    constructing the structure of the results in the output directory

    """
    def __init__(self, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir

    def iter_json_dir(self, input_dir):
        """Iterate through all json files in input_dir using a recursive walk"""
        for dirpath, dirnames, filenames in input_dir.walk(follow_symlinks=True):
            # calculate relative path
            dirpath = dirpath.absolute()
            try:
                dirpath = dirpath.relative_to(Path.cwd())
            except ValueError:
                pass

            # remove backwards relative
            dirpath = Path(*(p for p in dirpath.parts if p != ".."))
            for path in filenames:
                path = Path(path)
                if path.suffix == ".json":
                    yield Path(dirpath) / path

    def iter_results_dir(self):
        """ Iterate through all "leaf" result directories"""
        for dirpath, dirnames, filenames in self.output_dir.walk():
            if "input.json" in filenames:
                yield dirpath

    def _test_output_path(self, path, parser_name):
        path = Path(path)
        output_dir = self.output_dir / path
        return output_dir / Path(f"{parser_name}.json")

    def test_parser_path(self, path, parser_name):
        return self._test_output_path(path, parser_name)

    def test_file_path(self, path):
        return self._test_output_path(path, "input")


class Analyzer():
    """ Class for analys parser results save to output_dir"""
    def __init__(self, output_dir):
        self.tree = OutputTree(output_dir)

    def run(self, diff_ignore_order=False):
        """Run amalysis on all results in output_dir, format output
        as json and print to stdout"""
        print("[")
        first = True
        # for each result directory
        for item in self.tree.iter_results_dir():
            diffs = {}
            errors = {}
            orig = None

            for result in item.iterdir():
                with open(result, "rb") as f:
                    s = f.read()
                if result.name == "vista.json" and s.startswith(b"{["):
                    # strip outer braces
                    s = s[1:-1]
                s = s.strip()
                try:
                    # liberally parse the parser's json output
                    o = parser.parse_expression(s)

                except (ValueError, RecursionError) as e:
                    o = None
                    logger.info("failed to parse json at %s: %s",
                                result, e)
                    errors[result.name] = f"parse error: {e.__dict__}"
                if result.name == "input.json":
                    orig = o
                else:
                    diffs[result.name] = o
            results = []
            # run diff against all results
            for k, v in diffs.items():
                if k not in errors:
                    args = {
                        "get_deep_distance": True,
                        "ignore_encoding_errors": True,
                        "ignore_string_case": True,
                    }
                    if diff_ignore_order:
                        args["ignore_order"] = True
                    res = deepdiff.DeepDiff(orig, v, **args)
                else:
                    res = errors[k]
                results.append({"parser": k, "results": res})
            # don't print comma if first in list
            if first:
                first = False
            else:
                print(",")
            print('{"file":', '"' + str(item) + '"', ', "results": ',
                  flush=True)
            print(json.dumps(results, sort_keys=True, indent=1,
                             cls=ResultEncoder), "}", flush=True)
        print("]")


class TestManager():
    """Class for managing parser echo tests. Client is an intantiation
    of EchoClient, input_dir is a directory containing the json files
    to be test and output_dir is where to write the parsing results"""
    def __init__(self, client, input_dir, output_dir):
        self.tree = OutputTree(output_dir)
        self.input_dir = input_dir
        self.client = client

    def test_file(self, path, force=False):
        """Run the file at path through all the different parsers and
        save the results in a single directory named after `path`"""
        if str(path).startswith("/"):
            dst = Path(str(path)[1:])
        else:
            dst = path
        test_file_path = self.tree.test_file_path(dst)

        # parent = test_file_path.parent
        logger.info("running echo test for %s", path)

        # make result directory
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        # save input file
        shutil.copyfile(path, test_file_path)
        # run test against all parsers
        for ehr in EHRMapping.iter_unique():
            output_file = self.tree.test_parser_path(dst, ehr.parser)
            if output_file.exists() and not force:
                logger.info("results for %s exists, skipping", output_file)
                continue
            with open(path, "rb") as f:
                r, v = self.client.post(ehr, f.read())
            if r and r.ok:
                logger.info("writing results %s", output_file)
                logger.debug("%s: %s", ehr.parser, v)
                with open(output_file, "wb") as f:
                    f.write(v)

    def run(self, force):
        """ Run test on every file in intput dir"""
        for p in self.tree.iter_json_dir(self.input_dir):
            self.test_file(p, force)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="enable verbose logging")
@click.option("-d", "--debug", is_flag=True, help="enable debugging logging")
def cli(verbose, debug):
    """Process logging options. Note that if any of the options is
    enabled, the json output of the parse command will be unparsable"""
    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)



@cli.command()
@click.option("-i", "--input", type=click.Path(dir_okay=False, path_type=Path, readable=True), default="output.json", help="Path to json file generated by `analyze` command")
def filter(input):
    """Command to filter entries where no diff exists out of
    json-formatted alnalysis results"""
    with open(input, "r") as f:
        data = json.load(f)
    filtered = []
    for file_diff in data:
        has_diff = False
        for result  in file_diff["results"]:
            if result["results"]:
                has_diff = True
                break
        if has_diff:
            filtered.append(file_diff)
    print(json.dumps(filtered, indent=1))

@cli.command()
@click.option("-o", "--output-dir", type=click.Path(file_okay=False, path_type=Path, writable=True), default="output",
              help="directory to save testing output")
@click.option("--ignore-order", is_flag=True, help="Ignore order when performing deep diff")
def analyze(output_dir, ignore_order):
    """Analyze parser results and print a json representation of how
    each parser's result differs from the input file to stdout"""
    a = Analyzer(output_dir)
    a.run(ignore_order)


@cli.command()
@click.option("-i", "--input-dir", type=click.Path(file_okay=False, path_type=Path, readable=True), help="directory containing json files to be tested, will recursivel walk", required=True)
@click.option("-o", "--output-dir", type=click.Path(file_okay=False, path_type=Path, writable=True), default="output",
              help="directory to save testing output")
@click.option("-p", "--pythonurl", default="http://localhost:8484", help="Base url of python parser")
@click.option("-c", "--clojureurl", default="http://localhost:8282", help="Base url of clojure parser")
@click.option("-v", "--vistaurl", default="http://localhost:8383", help="Base url of vista parser")
@click.option("-j", "--javaurl", default="http://localhost:8181", help="Base url of java parsers")
@click.option("-f", "--force", is_flag=True, help="force recreation of result file even if it exists")
def parse(input_dir, output_dir, pythonurl, clojureurl, vistaurl, javaurl, force):
    """Run all json files nested in output_dir through each parser
    variant and save results to output_dir. output_dir's structure is
    that a directory tree is created for each input file, with a
    structure determined by the input file's path and "leaf" directory
    that matches the input file's name. Inside that files are the
    resulting echos from each parser, named after the parser, and an
    `input.json` containing a copy of the origional json file.

    """
    client = EchoClient(javaurl, vistaurl, clojureurl, pythonurl)
    mgr = TestManager(client, input_dir, output_dir)
    mgr.run(force)


if __name__ == "__main__":
    cli()
