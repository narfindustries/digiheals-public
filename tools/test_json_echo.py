#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
A python script for testing json echo servers in bulk
"""

import click
from clients.echo_clients import EchoClient, EHRMapping
from pathlib import Path
from datetime import datetime
import os
import shutil
import logging
import deepdiff
from utils import parser

logger = logging.getLogger(__name__)
logging.basicConfig()

class OutputTree():

    def __init__(self, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir


    def iter_json_dir(self, input_dir):
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
    def __init__(self, output_dir):
        self.tree = OutputTree(output_dir)

    def run(self):
        for item in self.tree.iter_results_dir():
            print("----", item, "----")
            diffs = {}
            orig = None
            for result in item.iterdir():
                with open(result, "rb") as f:
                    s = f.read()
                if result.name == "vista.json" and s.startswith(b"{["):
                    # strip outer braces
                    s = s[1:-1]
                try:
                    o = parser.parse_expression(s)

                except (ValueError, RecursionError):
                    continue
                if result.name == "input.json":
                    orig = o
                else:
                    diffs[result.name] = o

            for k, v in diffs.items():
                print(k, deepdiff.DeepDiff(orig, v))


class TestManager():
    def __init__(self, client, input_dir, output_dir):
        self.tree = OutputTree(output_dir)
        self.input_dir = input_dir
        self.client = client

    def test_file(self, path, force=False):
        if str(path).startswith("/"):
            dst = Path(str(path)[1:])
        else:
            dst = path
        test_file_path = self.tree.test_file_path(dst)
        if test_file_path.exists() and not force:
            logger.error("results for %s exists, skipping", path)
        # parent = test_file_path.parent
        logger.info("running echo test for %s", path)


        # make result directory
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        # save input file
        shutil.copyfile(path, test_file_path)
        # run test against all parsers
        results = self.client.post_all(path)
        for k, v in results.items():
            output_file = self.tree.test_parser_path(dst, k)
            logger.info("writing results %s", output_file)
            logger.debug("%s: %s", k, v)
            with open(output_file, "wb") as f:
                f.write(v)

    def run(self, force):
        for p in self.tree.iter_json_dir(self.input_dir):
            self.test_file(p, force)


@click.group()
@click.option("-v", "--verbose", is_flag=True)
@click.option("-d", "--debug", is_flag=True)
def cli(verbose, debug):
    if verbose:
        logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)



@cli.command()
@click.option("-o", "--output-dir", type=click.Path(file_okay=False, path_type=Path, writable=True), default="output",
              help="directory to save testing output")
def analyze(output_dir):
    a = Analyzer(output_dir)
    a.run()

@cli.command()
@click.option("-i", "--input-dir", type=click.Path(file_okay=False, path_type=Path, readable=True), help="directory containing json files to be tested, will recursivel walk", required=True)
@click.option("-o", "--output-dir", type=click.Path(file_okay=False, path_type=Path, writable=True), default="output",
              help="directory to save testing output")
@click.option("-p", "--pythonurl", default="http://localhost:8484")
@click.option("-c", "--clojureurl", default="http://localhost:8282")
@click.option("-v", "--vistaurl", default="http://localhost:8383")
@click.option("-j", "--javaurl", default="http://localhost:8181")
@click.option("-f", "--force", is_flag=True)
def parse(input_dir, output_dir, pythonurl, clojureurl, vistaurl, javaurl, force):
    client = EchoClient(javaurl, vistaurl, clojureurl, pythonurl)
    mgr = TestManager(client, input_dir, output_dir)
    mgr.run(force)

if __name__ == "__main__":
    cli()
