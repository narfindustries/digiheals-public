#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#

import json
from flask import Flask, request
from flask import jsonify


app = Flask(__name__)
@app.route("/gnuhealthecho",  methods=['POST'])
def echo_json():
    data = json.loads(request.get_data())
    return jsonify(data)
