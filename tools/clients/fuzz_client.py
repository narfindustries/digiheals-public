#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for the fuzzing server
"""

import click
import json
import requests
from pathlib import Path
import time

class FuzzClient():
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, url):
        """Constructor"""
        self.url = url

    def _request(self, filename, path, params=None):
        params = {} if params is None else params
        url = f"{self.url}/{path}/{filename}"
        try:
            r = requests.get(url, params=params, timeout=100)
        except Exception as e:
            return (-1, str(e))
        return (r.status_code, r.json())

    def fuzz(self, filename, seed=None):
        params = {} if seed is None else {"seed": seed}
        return self._request(filename, "fuzz", params)

    def pending_fuzz(self, filename):
        return self._request(filename, "pending_fuzz")

    def fuzz_terminated(self, filename):
        res, data = self.pending_fuzz(filename)
        return res != 200 or data.get("result", False) == False

    def wait_until_done(self, filename):
        done = False
        while not done:
            done = self.fuzz_terminated(filename)
            if not done:
                time.sleep(0.25)


@click.command()
@click.option("-f", "--file", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, multiple=True)
@click.option("-u", "--url", default="http://localhost:9000")
def cli_options(file, url):
    """
    Send a fuzz request for all --file arguments
    """
    print("fuzzing", file)
    client = FuzzClient(url)
    for f in file:
        code, data = client.fuzz(f.name)
        print(code, data)


if __name__ == "__main__":
    cli_options()
