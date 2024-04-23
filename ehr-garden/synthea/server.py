#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""

"""
from flask import Flask
from flask import jsonify
import os
import json

app = Flask(__name__)


@app.route("/")
def hello_world():
    files_original = os.listdir("/synthea/output/ccda/")
    os.system("./gradlew run")
    new_file = list(set(os.listdir("/synthea/output/ccda/")) - set(files_original))[0]
    filename = new_file.split(".")[0]
    json_file = {"filename": f"{filename}.json"}
    return jsonify(json_file)
