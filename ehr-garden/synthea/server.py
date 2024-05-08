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
    output_dir = "/synthea/output/ccda/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    files_original = os.listdir(output_dir)
    os.system("./gradlew run")
    new_file = list(set(os.listdir("/synthea/output/ccda/")) - set(files_original))[0]
    filename = new_file.split(".")[0]
    json_file = {"filename": f"{filename}.json"}
    return jsonify(json_file)


@app.route("/status")
def status():
    json_file = {"status": "ok"}
    return jsonify(json_file)


@app.route("/cleanup/<filename>")
def clean_test_files(filename):
    fhir_file = "/synthea/output/fhir/" + filename
    ccda_file = "/synthea/output/ccda/" + filename.split(".")[0] + ".xml"

    try:
        os.remove(fhir_file)
        print(f"Deleted file: {fhir_file}")
    except FileNotFoundError:
        print("Error deleting fhir file")

    try:
        os.remove(ccda_file)
        print(f"Deleted file: {ccda_file}")
    except FileNotFoundError:
        print("Error deleting fhir file")

    return jsonify(success=True)
