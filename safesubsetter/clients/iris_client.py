#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Create a Client for iris that can create patients and pull data
"""
import json
import click
import requests
from abstract_client import AbstractClient
from defusedxml.ElementTree import parse, ParseError
import xml.etree.ElementTree as ET


class IrisClient(AbstractClient):
    """Allow users to easy create a new patient and export all patients"""

    def __init__(self, fhir, base):
        """Constructor"""
        self.fhir = fhir
        self.base = base

    def export_patients(self, file_type=None):
        """Calls the FHIR API to export all patients"""
        if file_type is None:
            # Used for checking network/default
            file_type = "json"
        header_text = "application/fhir+" + file_type
        headers = {"Accept": header_text}
        tag = "default_tag"
        try:
            r = requests.get(
                f"{self.fhir}/{self.base}/Bundle?_tag={tag}&_sort=-_lastUpdated&_count=1",
                headers=headers,
                timeout=100,
                verify=False,
            )
            if file_type == "json":
                response_data = r.json()
            else:
                response_data = r.text
            return (r.status_code, response_data)
        except Exception as e:
            return (-1, str(e))

    def export_patients_tag(self, tag=None, file_type=None):
        """Calls the FHIR API to export all patients"""
        if file_type is None:
            # Used for checking network/default
            file_type = "json"
        header_text = "application/fhir+" + file_type
        headers = {"Accept": header_text}
        try:
            r = requests.get(
                f"{self.fhir}/{self.base}/Bundle?_tag={tag}&_sort=-_lastUpdated&_count=1",
                headers=headers,
                timeout=100,
                verify=False,
            )
            if file_type == "json":
                response_data = r.json()
            else:
                response_data = r.text
            return (r.status_code, response_data)
        except Exception as e:
            return (-1, str(e))

    def export_patient(self, p_id, file_type):
        """Calls the FHIR API to export patients with given ID"""
        header_text = "application/fhir+" + file_type
        headers = {"Accept": header_text}
        r = requests.get(
            f"{self.fhir}/{self.base}/Bundle/{p_id}",
            headers=headers,
            timeout=100,
            verify=False,
        )
        if file_type == "json":
            response_data = r.json()
        else:
            response_data = r.text
        return (r.status_code, response_data)

    def __get_new_patient_id(self, file_type, name, before_data=None):
        """Get the patient ID by pulling full list of patients before and after"""
        # differentiate between the patient files with and without the tag
        # if a tag is provided, then export patient with tag, else call the previously used endpoint
        if name == "default_tag":
            (_, after_data) = self.export_patients(file_type)
            if file_type == "json":
                if len(after_data["entry"]) == 1:  # Expectation is only one entry
                    return after_data["entry"][0]["resource"]["id"]

                for entry in after_data["entry"]:
                    if entry not in before_data["entry"]:
                        return entry["resource"]["id"]

            else:
                ns = {"fhir": "http://hl7.org/fhir"}

                after_root = ET.fromstring(after_data)

                total = after_root.find("fhir:total", ns)
                if total is not None and int(total.attrib.get("value", 0)) == 1:
                    pid = after_root.find(
                        "fhir:entry/fhir:resource/fhir:Bundle/fhir:id", ns
                    )
                    if pid is not None:
                        return pid.attrib.get("value")

                before_ids = []
                after_ids = []

                before_root = ET.fromstring(before_data)

                before_entries = before_root.findall(
                    "fhir:entry/fhir:resource/fhir:Bundle/fhir:id", ns
                )
                for entry in before_entries:
                    before_ids.append(entry.attrib.get("value"))

                after_entries = after_root.findall(
                    "fhir:entry/fhir:resource/fhir:Bundle/fhir:id", ns
                )
                for entry in after_entries:
                    after_ids.append(entry.attrib.get("value"))

                return list(set(after_ids) - set(before_ids))[0]
        else:
            (_, output_data) = self.export_patients_tag(name, file_type)
            if file_type == "json":
                if len(output_data["entry"]) == 1:  # Expectation is only one entry
                    return output_data["entry"][0]["resource"]["id"]

    def create_patient_fromfile(self, file, file_type, name=None):
        """Create a new patient from a FHIR JSON file"""
        (_, before_data) = self.export_patients(file_type)
        headers = {
            "Accept": f"application/fhir+{file_type}",
            "Content-Type": f"application/{file_type}",
        }
        r = requests.post(
            f"{self.fhir}/{self.base}/Bundle",
            data=file.read(),
            timeout=60,
            headers=headers,
            verify=False,
        )
        patient_id = None
        if r.status_code == 201:
            patient_id = self.__get_new_patient_id(
                file_type, "default_tag", before_data
            )
        return (patient_id, r)

    def create_patient(self, data, file_type, name):
        """Create a new patient from a FHIR JSON file"""
        headers = {
            "Accept": f"application/fhir+{file_type}",
            "Content-Type": f"application/fhir+{file_type}",
        }
        if file_type == "json" and isinstance(data, dict):
            data = json.dumps(data)
        r = requests.post(
            f"{self.fhir}/{self.base}/Bundle",
            data=data,
            timeout=100,
            headers=headers,
            verify=False,
        )
        patient_id = None
        if r.status_code == 201:
            patient_id = self.__get_new_patient_id(file_type, name)
        else:
            return (None, r.text)
        return (patient_id, r)

    def step(self, step_number: int, data, file_type, name):
        """
        Called from the GoT scripts
        If its the first step, we just got a FHIR JSON file from Synthea.
        We must extract the patient data from it.
        If not, then we can import the file as is
        """
        patient_id = None
        resp_or_err = {}
        if step_number == 0:
            if file_type == "json":
                try:
                    patient_data = json.loads(data)
                    (patient_id, resp_or_err) = self.create_patient(
                        json.dumps(patient_data), file_type, name
                    )
                except json.JSONDecodeError:
                    raise click.BadParameter("Malformed input json file.")
            else:
                (patient_id, resp_or_err) = self.create_patient(data, file_type, name)

        if patient_id is None:
            if file_type == "json":
                response = resp_or_err
            else:
                response = "<root></root>"
            return (patient_id, response, None)

        (_, export_response) = self.export_patient(patient_id, file_type)
        return_response = resp_or_err if file_type == "json" else "<root></root>"
        return (patient_id, return_response, export_response)


@click.command()
@click.option("--file", type=click.File("r"))
def cli_options(file):
    """
    Extract command-line arguments to either create a new patient
    No arguments: exports all patients in a JSON form
    """
    client = IrisClient("https://localhost:8007", "fhir/r4")
    if file is None:
        name = "placeholder"
        status, response = client.export_patients(name)
        if status == 200:
            print(response.text)
        else:
            print(status)
    else:
        try:
            parse(file)
            file_type = "xml"
        except ParseError:
            file_type = "json"

        if isinstance(file, str):
            with open(file, "r") as f:
                file = f.read()
        else:
            file.seek(0)
            file = file.read()

        _, r = client.create_patient_fromfile(file, file_type)
        print(r.text)


if __name__ == "__main__":
    cli_options()
