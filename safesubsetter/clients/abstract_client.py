#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""
Define an abstract class to all the other clients have the same set of methods
"""
from abc import ABCMeta, abstractmethod


class AbstractClient(metaclass=ABCMeta):
    """Ensure that these methods are implemented in each implementation"""

    @abstractmethod
    def __init__(self, fhir, base):
        """Constructor to ensure that we get the FHIR URL and API base URL"""

    @abstractmethod
    def export_patients(self):
        """Extracts Patient data using a FHIR output"""

    @abstractmethod
    def create_patient_fromfile(self, file):
        """A function that creates a user by sending a FHIR JSON object or uploading a CCDA file"""

    @abstractmethod
    def create_patient(self, data):
        """A function that creates a user by sending a FHIR JSON object or uploading a CCDA file"""

    @abstractmethod
    def export_patient(self, p_id):
        """Extracts one Patient data using a FHIR output"""
