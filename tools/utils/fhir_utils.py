"""Common FHIR functions used across modules """

import csv

# Common file paths
RESOURCES_FOLDER = "output/resource"
TYPES_FOLDER = "output/types"
SERVER_NAME = "ibm"

# Define the expected types and regex patterns
# xhtml is not included as regex is not defined
FHIR_TYPES = {
    "unsignedInt": {"type": "integer", "regex": "[0]|([1-9][0-9]*)"},
    "boolean": {"type": "boolean", "regex": "true|false"},
    "uri": {"type": "string", "regex": "\S*"},
    "url": {"type": "string", "regex": "\S*"},
    "string": {"type": "string", "regex": "[ \r\n\t\S]+"},
    "base64Binary": {"type": "string", "regex": "(\s*([0-9a-zA-Z\+\=]){4}\s*)+"},
    "date": {
        "type": "date",
        "regex": "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1]))?)?",
    },
    "uuid": {
        "type": "string",
        "regex": "urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    },
    "decimal": {
        "type": "decimal",
        "regex": "-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?",
    },
    "dateTime": {
        "type": "datetime",
        "regex": "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1])(T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00)))?)?)?",
    },
    "positiveInt": {"type": "integer", "regex": "\+?[1-9][0-9]*"},
    "time": {
        "type": "time",
        "regex": "([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?",
    },
    "code": {"type": "string", "regex": "[^\s]+(\s[^\s]+)*"},
    "oid": {"type": "string", "regex": "urn:oid:[0-2](\.(0|[1-9][0-9]*))+"},
    "instant": {
        "type": "datetime",
        "regex": "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))",
    },
    "integer": {"type": "integer", "regex": "[0]|[-+]?[1-9][0-9]*"},
    "markdown": {"type": "string", "regex": "\s*(\S|\s)*"},
    "canonical": {"type": "string", "regex": "\S*"},
    "id": {"type": "string", "regex": "[A-Za-z0-9\-\.]{1,64}"},
    "largeString": {"type": "largestring", "value": "A" * 1024},
    "largeInt": {"type": "largeinteger", "value": 2**200},
    "largeFloat": {"type": "largefloat", "value": 1.7976931348623157e308},
}


def parse_fhir_spec_csv(file_path):
    """Parse CSV file to extract all fields and their types and store as metadata."""
    metadata_fundamental = {}
    metadata_recursive = {}

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                field, field_type = row
                if field_type[0].islower():
                    metadata_fundamental[field] = {"type": field_type}
                elif field_type[0].isupper() and field_type.isalnum():
                    metadata_recursive[field] = {"type": field_type}

    return metadata_fundamental, metadata_recursive


class EfficientSSNGenerator:
    """Random SSN generator class"""

    def __init__(self):
        self.current_num = 1010001

    def get_next_ssn(self):
        """Increments to return the next randomly generated SSN"""
        while self.current_num <= 999999999:
            ssn_str = f"{self.current_num:09d}"
            area = ssn_str[:3]
            group = ssn_str[3:5]
            serial = ssn_str[5:]

            if area == "666":
                self.current_num = 667000000
                continue
            elif area.startswith("9"):
                raise ValueError("Reached invalid 900+ area numbers")

            if group == "00":
                self.current_num += 1000
                continue

            if serial == "0000":
                self.current_num += 1
                continue

            if area in ["000", "734", "749", "772"]:
                self.current_num += 1000000
                continue

            result = f"{area}-{group}-{serial}"
            self.current_num += 1
            return result

        raise ValueError("Exhausted all possible SSNs")


def ssn_gen():
    """Function to generate a unique, valid SSN"""
    ssn_generator = EfficientSSNGenerator()
    return ssn_generator.get_next_ssn()
