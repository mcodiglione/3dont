from . import Classes as cl
from . import aws_iot_interface as aws
import os
import importlib
import inspect
import ast
import logging
import subprocess
import SPARQLWrapper
import datetime
import owlready2 as owl2

# QUESTE FUNZIONI LEGGONO DIRETTAMENTE DA AWS IOT CORE, INCLUDENDO LE FUNZIONI DEDICATE.


def RDF_link_sensor_to_object(ontosensor, ontoobject):
    ontosensor.Contains_dynamic_original_data_relative_to.append(ontoobject)
    ontosensor.Contains_dynamic_data_relative_to.append(ontoobject)
    ontosensor.Contains_data_relative_to.append(ontoobject)
    ontoobject.Is_dynamically_originally_described_by.append(ontosensor)
    ontoobject.Is_dynamically_described_by.append(ontosensor)
    ontoobject.Is_described_by.append(ontosensor)
    return


def RDF_add_sensor_to_graph(SensorMetadata, onto, populated_namespace):
    aws.setup_sensor_connection(SensorMetadata)
    sensor_name = SensorMetadata.name
    object_name = SensorMetadata.DescribedObject
    property_name = SensorMetadata.properties
    sensor = onto.Sensor_Datastream(f"{sensor_name}", namespace=populated_namespace)
    object = getattr(onto, object_name)
    RDF_link_sensor_to_object(sensor, object)
    value_dict = aws.get_sensor_data_from_name(
        sensor_name
    )  # lo storico qui viene aggiornato automaticamente
    setattr(sensor, property_name, value_dict["Value"])
    sensor.Acquisition_Time = value_dict["AcquisitionTime"]
    sensor.is_a.append(onto.Dynamic_Import)
    sensor.is_a.append(onto.Data_Import)
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
    for sensor in onto.Sensor_Datastream.instances():
        RDF_update_sensor_value(sensor.name, onto)
    return


def RDF_manual_annotation(args: cl.Args, subject, predicate, object, author_name):
    onto = args.onto
    pop_namespace = args.populated_base
    with onto:
        # check_for_number
        starting_n = 1
        while getattr(onto, f"Manual_Annotation_number_{starting_n}_"):
            starting_n += 1
        n = starting_n
        annotation_name = f"Manual_Annotation_number_{n}_"
        annotation = onto.Manual_Annotation(annotation_name, namespace=pop_namespace)
        # rdf:type
        annotation.is_a.append(onto.Static_Import)
        annotation.is_a.append(onto.Data_Import)
        # author
        annotation.Annotation_Author = author_name
        # time
        time = datetime.datetime.now()
        annotation.Acquisition_Time = time
        # subject
        annotation.Contains_static_original_data_relative_to.append(subject)
        annotation.Contains_static_data_relative_to.append(subject)
        annotation.Contains_data_relative_to.append(subject)
        subject.Is_statically_originally_described_by.append(annotation)
        subject.Is_statically_described_by.append(annotation)
        subject.Is_described_by.append(annotation)
        # if predicate is data prop object is type str
        xsd = owl2.default_world.get_namespace("http://www.w3.org/2001/XMLSchema#")
        if not type(object) == str:
            try:
                predicate[annotation] = object
            except:
                predicate[annotation].append(object)
        elif xsd.string in predicate.range:
            try:
                predicate[annotation] = object
            except:
                predicate[annotation].append(object)
        elif xsd.integer in predicate.range:
            try:
                predicate[annotation] = int(object)
            except:
                predicate[annotation].append(int(object))
        else:
            try:
                predicate[annotation] = float(object)
            except:
                predicate[annotation].append(float(object))


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
                if func_name.startswith("SENSOR_"):
                    func = getattr(module, func_name)
                    if inspect.isfunction(func):
                        try:
                            func(base, populated_base, onto)
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
    clear_query = f"CLEAR GRAPH <{GRAPH_URI}>"
    create_query = f"CREATE GRAPH <{GRAPH_URI}>"

    # wrapper.setQuery(check_query)
    # result = wrapper.query().convert().decode("utf-8")

    try:
        wrapper.setMethod(SPARQLWrapper.POST)
        print("wrapper set to 'post'")
        wrapper.setQuery(create_query)
        print("create query execution")
        wrapper.query()
        print("Graph Created!")
        wrapper.addNamedGraph(str(GRAPH_URI))
        wrapper.setMethod(SPARQLWrapper.GET)
    except:
        wrapper.setQuery(clear_query)
        print("clear query execution")
        wrapper.query()
        print("Graph Cleared!")
        wrapper.setMethod(SPARQLWrapper.GET)
