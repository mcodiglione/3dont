"""
cose da fare per integrazione con interfaccia centrale:
- aggiungere pulsante di ADD_SENSOR in cui si chiama RDF_add_sensor_to_graph() e poi si salva l'oggetto onto
    - capire come far sì che l'utente possa facilmente configurare un'istanza della classe di SensorMetadata
- aggiungere pulsante, cliccabile dopo che viene caricato un certo grafo, chiamato UPDATE_SENSORS_AND_REASON, che chiami RDF_update_all_sensors e RDF_sensor_reasoning, poi salvando l'oggetto onto
-
"""

from . import Classes as cl
from . import RDF_functions as RDF


def set_SensorMetadata(
    args: cl.Args,
):  # questo lo dovrei implementare come costruttore interno alla classe ma ormai è così, sticazzi
    CertBundle = cl.SensorCertBundle(
        args.cert_pem_path,
        args.private_key_path,
        args.root_ca_path,
        args.client_id,
        args.mqtttopic,
    )
    SensorMetadata = cl.SensorMetadata(
        args.sensor_name, args.property_name, args.object_name, CertBundle
    )
    return SensorMetadata


def command_add_sensor(args: cl.Args):
    SensorMetadata = set_SensorMetadata(args)
    RDF.RDF_add_sensor_to_graph(SensorMetadata, args.onto, args.populated_namespace)
    print("sensor added")
    onto = args.onto
    onto.save(args.pop_ont_path)
    print("onto saved")
    RDF.RDF_check_and_create_graph(args.graph_uri, args.wrapper)
    RDF.RDF_upload_rdf(args.pop_ont_path, args.graph_uri, args.virtuoso_isql)
    print("RDF uploaded into virtuoso")
    return


def command_update_sensors(args: cl.Args):
    RDF.RDF_update_all_sensors(args.onto)
    print("sensors updated")
    onto = args.onto
    onto.save(args.pop_ont_path)
    print("onto saved")
    RDF.RDF_check_and_create_graph(args.graph_uri, args.wrapper)
    RDF.RDF_upload_rdf(args.pop_ont_path, args.graph_uri, args.virtuoso_isql)
    print("RDF uploaded into virtuoso")
    return


def command_sensor_reason(args: cl.Args):
    RDF.RDF_sensor_reasoning(args.onto, args.base, args.populated_base, args.ont_path)
    print("reasoning executed")
    onto = args.onto
    onto.save(args.pop_ont_path)
    print("onto saved")
    RDF.RDF_check_and_create_graph(args.graph_uri, args.wrapper)
    RDF.RDF_upload_rdf(args.pop_ont_path, args.graph_uri, args.virtuoso_isql)
    print("RDF uploaded into virtuoso")
    return


def command_update_sensors_and_reason(args: cl.Args):  # faster, only saves at the end
    RDF.RDF_update_all_sensors(args.onto)
    print("sensors updated")
    RDF.RDF_sensor_reasoning(args.onto, args.base, args.populated_base, args.ont_path)
    print("reasoning executed")
    onto = args.onto
    onto.save(args.pop_ont_path)
    print("onto saved")
    RDF.RDF_check_and_create_graph(args.graph_uri, args.wrapper)
    RDF.RDF_upload_rdf(args.pop_ont_path, args.graph_uri, args.virtuoso_isql)
    print("RDF uploaded into virtuoso")
    return


def command_manual_annotation(args: cl.Args, subject, predicate, object, author_name):
    RDF.RDF_manual_annotation(args, subject, predicate, object, author_name)
    print("annotation recorded")
    RDF.RDF_sensor_reasoning(args.onto, args.base, args.populated_base, args.ont_path)
    print("reasoning executed")
    onto = args.onto
    onto.save(args.pop_ont_path)
    print("onto saved")
    RDF.RDF_check_and_create_graph(args.graph_uri, args.wrapper)
    RDF.RDF_upload_rdf(args.pop_ont_path, args.graph_uri, args.virtuoso_isql)
    print("RDF uploaded into virtuoso")
    return
