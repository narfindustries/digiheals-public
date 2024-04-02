#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
#
"""
Build clients for OpenEMR that can get the temporary authorization key
and send FHIR API requests using them.
"""
import random
import string
import requests
import jwt
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class OpenEMRClient:
    """Create an OpenEMR client using the necessary JWT values

    Prerequisites: you must have a keypair (RSA private and public keys)
    stored in id_rsa.pub and id_rsa files in the same folder.

    You will also need to extract the kid from the https://mkjwk.org/ output
    for the Keypair sets.
    """

    def __init__(self, kid: str, client_id: str, hostname: str):
        """Constructor"""
        self.hostname = hostname
        with open("id_rsa.pub", encoding="utf8") as f_pubfile:
            self.public_key = f_pubfile.read()

        with open("id_rsa", encoding="utf8") as f_privfile:
            self.private_key = f_privfile.read()

        self.headers = {"alg": "RS384", "typ": "JWT", "kid": kid}
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
            "scope": "api:fhir system/Patient.read system/Patient.$export",
            "client_assertion": authorization_key,
        }
        r = requests.post(
            f"{self.hostname}/oauth2/default/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            verify=False,
            timeout=1,
        )
        if r.status_code == 200:
            self.access_token = r.json()["access_token"]
        else:
            raise Exception("Access Token not received")

    def get_fhir_patients(self):
        """Request patients from the FHIR API using the access token"""
        assert self.access_token is not None
        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.get(
            f"{self.hostname}/apis/default/fhir/Patient",
            headers=headers,
            verify=False,
            timeout=1,
        )
        if r.status_code == 200:
            print(r.json())
        else:
            raise Exception("Patient Access Failed")

    def export_all_fhir_patients(self):
        """Bulk export option: https://github.com/openemr/openemr/blob/master/FHIR_README.md#bulk-fhir-exports"""
        assert self.access_token is not None
        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.get(
            f"{self.hostname}/apis/default/fhir/Patient/$export",
            headers=headers,
            verify=False,
            timeout=1,
        )
        if r.status_code == 200:
            print(r.json())
        else:
            raise Exception("Patient Access Failed")


def main():
    """Create an instance of the client and
    invoke the authorization token method.

    Invoking the get_fhir_patients() function or any other FHIR API
    request without first acquiring an access_token will fail.

    The access token is only usable for 300 seconds, and usable only once.
    """
    client = OpenEMRClient(
        "E6hXJBZXSh0FkmwUqQovT0vZSbKR-sr2WEPIV0b-joI",
        "dbmJyFsKgNh59JLh3fx0R48HKY2UO043Z3UfitIpKoE",
        "https://localhost",
    )
    client.get_authorization_token()
    client.get_fhir_patients()

    # Token has expired, generate one again
    client.get_authorization_token()
    client.export_all_fhir_patients()


if __name__ == "__main__":
    main()
