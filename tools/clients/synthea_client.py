#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for the synthea server
"""
import click
import requests

class SyntheaClient():
    """ Client for generating ehr documents via synthea"""
    def __init__(self, url):
        self.url = url

    def generate(self):
        try:
            r = requests.get(self.url, timeout=100)
        except Exception as e:
            return (-1, str(e))
        data = r.json()        
        return (r.status_code, data["filename"])
