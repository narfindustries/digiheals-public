#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""

"""
from flask import Flask, request
from flask import jsonify
import os
import json
from fuzzer import fuzz

app = Flask(__name__)
fhir_dir = "/synthea/output/fhir/"


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
    fhir_file = fhir_dir + filename
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


@app.route("/fuzz/<filename>")
def do_fuzz(filename):
    filepath = os.path.join(fhir_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "file not found"}), 400
    seed = request.args.get("seed", None)
    if seed is not None:
        seed = int(seed)
    sess = fuzz.JsonFuzzSession.get_session(filepath,
                                            filepath,
                                            seed=seed)
    events = sess.fuzz(int(request.args.get("count", 1)))
    return jsonify({
        "success": True,
        "results": [{"filename": event.filename,
                     "output_name": event.output_name} for event in events]
    })


def _is_fuzzing(filename):
    pending = []

    if filename is None:
        sessions = fuzz.JsonFuzzSession.all_sessions()
    else:
        filepath = os.path.join(fhir_dir, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "file not found", "success": False}), 400
        sess = fuzz.JsonFuzzSession.get_session(filepath, filepath)
        sessions = [sess] if sess else []
    for sess in sessions:
        pend = sess.pending_fuzzes
        pending += pending
    return jsonify({"result": bool(pending),
                    "success": True,
                    "count": len(pending),
                    "pending": [str(p) for p in pending]})


@app.route("/pending_fuzz/")
def is_fuzzing_any():
    return _is_fuzzing(None)


@app.route("/pending_fuzz/<filename>")
def is_fuzzing(filename):
    return _is_fuzzing(filename)
