import Classes as cl
import aws_iot_interface as aws
import os
import importlib
import inspect
import ast
import logging
import subprocess
import SPARQLWrapper

# QUESTE FUNZIONI LEGGONO DIRETTAMENTE DA AWS IOT CORE, INCLUDENDO LE FUNZIONI DEDICATE.
"""LE RELATIONSHIPS TRA OGGETTI E SENSORI SARANNO:
        - Sends_datastream_about
        - Is_dynamically_described_by
"""


def RDF_link_sensor_to_object(ontosensor, ontoobject):
    ontosensor.Sends_datastream_about.append(ontoobject)
    ontoobject.Is_dynamically_described_by.append(ontosensor)
    return


def RDF_add_sensor_to_graph(SensorMetadata, onto, populated_namespace):
    aws.setup_sensor_connection(SensorMetadata)
    sensor_name = SensorMetadata.name
    object_name = SensorMetadata.DescribedObject
    property_name = SensorMetadata.property
    sensor = onto.Sensors(f"{sensor_name}", namespace=populated_namespace)
    object = getattr(onto, object_name)
    RDF_link_sensor_to_object(sensor, object)
    value_dict = aws.get_sensor_data_from_name(
        sensor_name
    )  # lo storico qui viene aggiornato automaticamente
    setattr(sensor, property_name, value_dict["Value"])
    sensor.Acquisition_Time = value_dict["AcquisitionTime"]
    return


def RDF_update_sensor_value(sensor_name, onto):
    value_dict = aws.get_sensor_data_from_name(
        sensor_name
    )  # lo storico qui viene aggiornato automaticamente
    sensor = getattr(onto, sensor_name)
    property_name = value_dict["Property"]
    setattr(sensor, property_name, value_dict["Value"])
    sensor.Acquisition_Time = value_dict["AcquisitionTime"]
    return


def RDF_update_all_sensors(onto):
    for sensor in onto.Sensors.instances():
        RDF_update_sensor_value(sensor.name, onto)
    return


def RDF_update_sensors_from_object(object_name, onto):
    object = getattr(onto, object_name)
    for sensor in object.Is_dynamically_described_by:
        RDF_update_sensor_value(sensor.name)
    return


def RDF_sensor_reasoning(onto, base, populated_base, ont_path):
    file_content = None
    file_path = ont_path[:-4] + "_Rules.py"
    # Read the content of the Python file
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
    except:
        pass
    if file_content:
        # Parse the content to get the AST
        tree = ast.parse(file_content)

        # Define a visitor class to find function definitions
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.functions = []

            def visit_FunctionDef(self, node):
                self.functions.append(node.name)
                self.generic_visit(node)

        # Create a visitor and visit the AST nodes
        visitor = FunctionVisitor()
        visitor.visit(tree)
        # List of functions in the file
        functions = visitor.functions
        # Load the module dynamically
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(
            "WORK IN PROGRESS: geometric rules consider the dataset to be expressed in meters"
        )
        # Execute each function found in the module
        with onto:
            for func_name in functions:
                func = getattr(module, func_name)
                if inspect.isfunction(func):
                    try:
                        func(base, populated_base)
                        print(f"Sensor_Rule '{func_name}' executed")
                    except Exception as e:
                        print(f"Error executing function '{func_name}': {e}")
    return


def RDF_upload_rdf(file_path, GRAPH_URI, VIRTUOSO_ISQL):
    """Upload RDF file to the specified graph URI."""
    logging.basicConfig(level=logging.DEBUG)

    load_query = f"CALL DB.DBA.RDF_LOAD_RDFXML_MT (file_to_string_output('{file_path}'), '', '{GRAPH_URI}', 0, 8);"
    run_command = [f"{VIRTUOSO_ISQL}"]

    logging.debug(f"Executing command: {run_command}")

    try:
        process = subprocess.Popen(
            run_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(load_query)

        logging.debug(f"stdout: {stdout}")
        logging.error(f"stderr: {stderr}")

        if process.returncode != 0:
            logging.error(f"Command failed with return code {process.returncode}")
        else:
            logging.info("RDF upload completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


def RDF_check_and_create_graph(GRAPH_URI, wrapper):
    print("checking and creating graph")
    """Check if the graph exists and create it if not. Clear its content if it exists."""
    # check_query = "ASK WHERE {GRAPH <" f"{GRAPH_URI}>" + " {OPTIONAL { ?s ?p ?o }}}"
    clear_query = f"DROP GRAPH <{GRAPH_URI}>"
    create_query = f"CREATE GRAPH <{GRAPH_URI}>"

    # wrapper.setQuery(check_query)
    # result = wrapper.query().convert().decode("utf-8")

    try:
        wrapper.setMethod(SPARQLWrapper.POST)
        print("wrapper set to 'post'")
        wrapper.setQuery(clear_query)
        print("clear query execution")
        wrapper.query()
        print("Graph Dropped")
        wrapper.setQuery(create_query)
        wrapper.query()
        print("Graph Created")
        wrapper.addNamedGraph(str(GRAPH_URI))
        wrapper.setMethod(SPARQLWrapper.GET)
    except:
        wrapper.setMethod(SPARQLWrapper.POST)
        print("wrapper set to 'post'")
        wrapper.setQuery(create_query)
        print("create query execution")
        wrapper.query()
        print("Graph Created")
        wrapper.addNamedGraph(str(GRAPH_URI))
        wrapper.setMethod(SPARQLWrapper.GET)
