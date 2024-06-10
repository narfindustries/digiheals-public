#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a client for the json echoing servers
"""

import click
import json
import requests
from pathlib import Path
import time
import enum
import dataclasses
import logging

logger = logging.getLogger(__name__)
logging.basicConfig()

class Langs(enum.StrEnum):
    JAVA = "java"
    VISTA = "vista"
    CLOJURE = "clojure"
    PYTHON = "python"

    def __str__(self):
        return self.value

class EHRs(enum.StrEnum):
    IPM = "ibm"
    HAPI = "hapi"
    OPENMRS = "openmrs"
    VISTA = "vista"
    BLAZE = "blaze"
    GNUHEALTH = "gnuhealth"

    def __str__(self):
        return self.value


class Parsers(enum.StrEnum):
    PYTHON_JSON = "python"
    CLOJURE_JSON = "clojure.data"
    VISTA_JSON = "vista"
    MUMPS_JSON = "mumps"
    FASTERXML = "fasterxml.jackson"
    JAKARTA = "jakarta"

    def __str__(self):
        return self.value


@dataclasses.dataclass(frozen=True, eq=True)
class EHRInfo:
    ehr: EHRs
    language: Langs
    parser: Parsers


class EHRMapping:
    EHR_MAPPING = {}

    @classmethod
    def create(cls, ehr, lang, parser):
        cls.EHR_MAPPING[ehr] = EHRInfo(EHRs(ehr), Langs(lang), Parsers(parser))

    @classmethod
    def get(cls, name):
        return cls.EHR_MAPPING.get(str(name))

    @classmethod
    def iter_unique(cls):
        parsers = set()
        for ehr in cls.EHR_MAPPING.values():
            if ehr.parser not in parsers:
                yield ehr
                parsers.add(ehr.parser)

    @classmethod
    def iter_names(cls):
        for ehr in cls.EHR_MAPPING.values():
            yield ehr.ehr.value


EHRMapping.create("ibm", "java", "jakarta")
EHRMapping.create("hapi", "java", "fasterxml.jackson")
EHRMapping.create("openmrs", "java", "fasterxml.jackson")
EHRMapping.create("vista", "vista", "vista")
EHRMapping.create("blaze", "clojure", "clojure.data")
EHRMapping.create("gnuhealth", "python", "python")


class EchoClient():
    def __init__(self, javaurl="http://localhost:8181",
                 vistaurl="http://localhost:8383",
                 clojureurl="http://localhost:8282",
                 pythonurl="http://localhost:8484"):
        self.javaurl = javaurl
        self.vistaurl = vistaurl
        self.clojureurl = clojureurl
        self.pythonurl = pythonurl


    def post(self, who, data):
        if not isinstance(who, EHRInfo):
            who = EHRMapping.get(str(who))
        which = who.language
        url = getattr(self, which + "url") + f"/{who.ehr.value}echo"
        u = url
        # req =
        #prep = req.prepare()
        #s = requests.Session()
        try:
            r = requests.request("POST", url, data=data, stream=True, timeout=100)
            resp = b""
            for line in r.iter_lines():
                resp += line
        except Exception as e:
            logger.error("error connecting to %s at %s: %s", who.ehr, url, e)
            return None, None
        return r, resp

    def post_all(self, data):
        results = {}
        with open(data, "rb") as f:
            data = f.read()
        for ehr in EHRMapping.iter_unique():
            r, res = self.post(ehr, data)
            if r and r.ok:
                results[ehr.parser.value] = res
        return results


@click.command()
@click.option("-f", "--file", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, multiple=True)
@click.option("-p", "--pythonurl", default="http://localhost:8484")
@click.option("-c", "--clojureurl", default="http://localhost:8282")
@click.option("-v", "--vistaurl", default="http://localhost:8383")
@click.option("-j", "--javaurl", default="http://localhost:8181")
def cli_options(file, pythonurl, clojureurl, vistaurl, javaurl):
    client = EchoClient(javaurl, vistaurl, clojureurl, pythonurl)
    for f in file:
        results = client.post_all(f)
        print(results)


if __name__ == "__main__":
    cli_options()
