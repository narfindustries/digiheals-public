#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Regex to modify input patient file
"""
import re
import json


def replace_substring(input_string):
    """
    Replace substring in input string
    """
    part1, part2 = input_string.split("?identifier=")
    reference_value = part2.split("|")[-1]
    return f"{part1}/{reference_value}"


def modify_references_in_json(json_data):
    """
    Modify references in JSON object by recursion
    """
    reg_pattern = re.compile(
        r"(Organization|Location|Practitioner)\?identifier=[^\|]+\|[a-zA-Z0-9\-]+"
    )
    def recursive_modify(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "reference" and isinstance(value, str):
                    match = reg_pattern.search(value)
                    if match:
                        # Replace substring
                        data[key] = replace_substring(value)
                else:
                    recursive_modify(value)
        elif isinstance(data, list):
            for item in data:
                recursive_modify(item)

    recursive_modify(json_data)
    return json.dumps(json_data)
