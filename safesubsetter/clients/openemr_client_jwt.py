#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
#
"""
Build clients for OpenEMR that can get the temporary authorization key
and send FHIR API requests using them.
"""
import json
import random
import string
from pathlib import Path

import click
import jwt
import requests
from jwcrypto import jwk
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class OpenEMRClient:
    """Create an OpenEMR client using the necessary JWT values

    Prerequisites: you must have a keypair (RSA private and public keys)
    stored in keypair_set, private_key and public_key files in the same folder.

    """

    def __init__(self, client_id: str, hostname: str):
        """Constructor"""
        self.hostname = hostname

        with open("keypair_set", encoding="utf8") as key_file:
            self.keypair_set = json.loads(key_file.read())

        with open("private_key", "rb") as f_privfile:
            self.private_key = f_privfile.read()

        self.kid = self.keypair_set["keys"][0]["kid"]

        self.headers = {"alg": "RS384", "typ": "JWT", "kid": self.kid}
        self.payload = {
            "sub": client_id,
            "iss": client_id,
            "aud": f"{self.hostname}/oauth2/default/token",
        }
        self.access_token = None

    def get_new_key(self):
        """Create a key using the JWT library"""
        self.payload["jti"] = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=20)
        )
        encoded = jwt.encode(
            self.payload, self.private_key, algorithm="RS384", headers=self.headers
        )
        return encoded

    def get_authorization_token(self):
        """Use key and request an access token"""

        authorization_key = self.get_new_key()
        data = {
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "grant_type": "client_credentials",
            "scope": "openid offline_access api:oemr api:fhir api:port system/Patient.read system/DocumentReference.read system/DocumentReference.$docref system/Binary.read",
            "client_assertion": authorization_key,
        }
        r = requests.post(
            f"{self.hostname}/oauth2/default/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            verify=False,
            timeout=5,
        )
        if r.status_code == 200:
            self.access_token = r.json()["access_token"]
        else:
            raise Exception("Access Token not received")

    def get_fhir_patients(self):
        """Request patients from the FHIR API using the access token"""
        assert self.access_token is not None
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-type": "xml",
        }
        r = requests.get(
            f"{self.hostname}/apis/default/fhir/Patient",
            headers=headers,
            verify=False,
            timeout=5,
        )
        if r.status_code == 200:
            return r.json()
        else:
            print(r)
            raise Exception("Patient Access Failed")

    def export_fhir_patients_by_docref(self, patient):
        """Bulk export option:
        https://github.com/openemr/openemr/blob/master/FHIR_README.md#bulk-fhir-exports
        """
        assert self.access_token is not None
        headers = {"Authorization": f"Bearer {self.access_token}", "accept": "*/*"}
        r = requests.post(
            f"{self.hostname}/apis/default/fhir/DocumentReference/$docref",
            headers=headers,
            params={"patient": patient},
            verify=False,
            timeout=600,
        )
        if r.status_code == 200:
            return r.json()
        else:
            print(r)
            raise Exception("Docref creation failed")

    def download_ccda_files(self, document_id):
        """Bulk export option:"""
        assert self.access_token is not None
        headers = {"Authorization": f"Bearer {self.access_token}", "accept": "*/*"}
        r = requests.get(
            f"{self.hostname}/apis/default/fhir/Binary/{document_id}",
            headers=headers,
            verify=False,
            timeout=300,
        )
        if r.status_code == 200:
            return r
        else:
            print(r)
            raise Exception("CCDA file download failed")


def generate_keypair():
    """
    Generate keypairs using the jwk library
    Creates/overwrites three files
    """
    kid = "".join(random.choices(string.ascii_uppercase + string.digits, k=20))
    key = jwk.JWK.generate(kty="RSA", size=2048, alg="RS384", use="sig", kid=kid)
    public_key = key.export_public()
    private_key = key.export_private()
    keypair_set = {
        "keys": [eval(private_key)]
    }  # This is VERY bad. Shouldn't be using eval
    print(public_key, private_key, key.export_to_pem(True, None))
    with open("keypair_set", "w", encoding="utf8") as f_keypair:
        f_keypair.write(json.dumps(keypair_set))
    with open("private_key", "wb") as priv:
        priv.write(key.export_to_pem(True, None))
    with open("public_key", "wb") as pub:
        pub.write(key.export_to_pem(False, None))


@click.command()
@click.option("--clientid", required=True, help="Get Client ID cli argument")
@click.option("--url", required=True, help="Get URL of OpenEMR cli argument")
@click.option("--generate/--no-generate", default=False)
def openemr_client_instance(clientid, url, generate):
    """
    Defines the command-line interface used by this tool
    Performs two tasks: generates a new keypair
    This new keypair cannot be used right away as the keypair_set needs
    to be pasted on the registration UI on OpenEMR
    Grabs the clientID as an argument and tries to construct useful API queries
    """
    if generate:
        generate_keypair()

    client = OpenEMRClient(
        clientid,
        url,
    )
    client.get_authorization_token()
    patients = client.get_fhir_patients()  # Request #1
    for patient in patients["entry"]:
        """
        This is where things get a little complicated:
        1. Find the patient uuid from the total list of patients
        2. Create a CCDA document using a POST request. Takes a while
        3. Download the CCD document that was created
        4. Save the file in the ExportedCCDAFiles folder
        """
        patient_id = patient["resource"]["id"]

        # Request #2
        client.get_authorization_token()
        document_meta = client.export_fhir_patients_by_docref(patient_id)["entry"][0]
        document_id = document_meta["resource"]["id"]

        # Request #3
        client.get_authorization_token()
        downloaded_file = client.download_ccda_files(document_id)

        # Create a folder if we do not have it already
        Path("ExportedCCDAFiles").mkdir(parents=True, exist_ok=True)

        # Save the exported XML to file
        with open(
            f"ExportedCCDAFiles/{document_id}.xml", "w"
        ) as downloaded_file_writer:
            downloaded_file_writer.write(downloaded_file.text)


def main():
    """Create an instance of the client and
    invoke the authorization token method.

    Invoking the get_fhir_patients() function or any other FHIR API
    request without first acquiring an access_token will fail.

    The access token is only usable for 300 seconds, and usable only once.
    """

    openemr_client_instance()


if __name__ == "__main__":
    main()
