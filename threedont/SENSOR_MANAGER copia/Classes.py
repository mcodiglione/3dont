from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from owlready2.namespace import Ontology, Namespace
import SPARQLWrapper


class SensorMetadata:
    def __init__(self, name, prop, object_name, CertBundle, description=""):
        self.name = name
        self.description = description
        self.property = prop
        self.DescribedObject = object_name
        self.CertBundle = CertBundle
        pass


class SensorCertBundle:
    def __init__(
        self, cert_pem_path, private_key_path, root_ca_path, client_id, mqtttopic
    ):
        self.cert_pem = Path(cert_pem_path).read_text()
        self.private_key = Path(private_key_path).read_text()
        self.AmazonRootCA1_pem = Path(root_ca_path).read_text()
        self.client_id = client_id
        self.mqtttopic = mqtttopic
        pass


@dataclass
class Args:
    cert_pem_path: str = None
    private_key_path: str = None
    root_ca_path: str = None
    client_id: str = None
    mqtttopic: str = None
    sensor_name: str = None
    property_name: str = None
    object_name: str = None
    ont_path: str = None
    pop_ont_path: str = None
    onto: Ontology = None
    base: Namespace = None
    populated_base: Namespace = None
    graph_uri: str = None
    wrapper: SPARQLWrapper.Wrapper.SPARQLWrapper = None
    virtuoso_isql: str = None
