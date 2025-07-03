import logging
import sys
from queue import Queue
from urllib.error import URLError

from SPARQLWrapper.SPARQLExceptions import QueryBadFormed

from .db import SparqlEndpoint, WrongResultFormatException, EmptyResultSetException
from .viewer import Viewer, get_color_map
from ..gui import GuiWrapper
from .state import Project
from ..nl_2_sparql import nl_2_sparql, init_client

from ..sensor_manager import Sensor_Management_Functions as smf
from ..sensor_manager import Classes as cl
from ..sensor_manager import aws_iot_interface as aws
import owlready2 as owl2

__all__ = ["Controller"]

"""
    The commands_pipe will transport function calls from the GUI to the Controller.
    A functions here is a tuple of the form (function_name, args).
    ActionController is just a middleman to help with the transport between the processes, a facade.
"""

NUMBER_OF_LABELS_IN_LEGEND = 5


class ActionController:
    def __init__(self, commands_queue, start_func):
        self.commands_queue = commands_queue
        self._start = start_func

    def start(self):
        self._start()

    def __getattr__(self, item):
        # check if controller has the function
        if not hasattr(Controller, item) or not callable(getattr(Controller, item)):
            raise AttributeError(f"Controller has no method {item}")

        f = lambda *args: self.commands_queue.put((item, args))
        return f


def report_errors_to_gui(func):
    """
    Decorator to report errors to the GUI.
    """

    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except URLError as e:
            self.gui.set_statusbar_content(f"Connection error: {e}", 5)
            raise e
        except QueryBadFormed as e:
            response = str(e).split("Response:\n")[1]
            self.gui.set_query_error(f"Bad query: {response}")
            raise e
        except WrongResultFormatException as e:
            self.gui.set_query_error(f"Wrong result format: {e}")
            raise e
        except EmptyResultSetException as e:
            self.gui.set_query_error(f"Empty result set: {e}")
            raise e

    return wrapper


class Controller:
    def __init__(self, config, app_state):
        self.config = config
        self.app_state = app_state
        self.commands_queue = Queue()
        action_controller = ActionController(self.commands_queue, self.run_event_loop)
        self.gui = GuiWrapper(action_controller, sys.argv)
        viewer_server_port = self.gui.get_viewer_server_port()
        self.viewer_client = Viewer(viewer_server_port)
        self.sparql_client = None
        self.Args = cl.Args()
        self.project = None

    def stop(self):
        print("Stopping controller...")
        self.commands_queue.put(None)

    def run(self):
        # this will create a thread that runs `run_event_loop`
        self.gui.run()

    def run_event_loop(self):
        print("Running controller")
        self.update_project_list()
        if self.config.get_general_loadLastProject():
            last_project = self.app_state.get_projectName()
            if last_project and Project.exists(last_project):
                self.open_project(last_project)

        command = self.commands_queue.get()
        while command is not None:
            function_name, args = command
            try:
                getattr(self, function_name)(*args)
            except Exception:
                logging.exception(
                    "Error in controller running function %s", function_name
                )

            command = self.commands_queue.get()

    @report_errors_to_gui
    def select_query(self, query):
        print("Controller: ", query)
        if self.sparql_client is None:
            print("No connection to server")
            return

        colors = self.sparql_client.execute_select_query(query)
        self.viewer_client.attributes(colors)
        self.viewer_client.set(curr_attribute_id=0)

    @report_errors_to_gui
    def scalar_query(self, query):
        print("Controller: ", query)
        if self.sparql_client is None:
            print("No connection to server")
            return

        scalars = self.sparql_client.execute_scalar_query(query)
        self.viewer_client.attributes(self.sparql_client.colors, scalars)
        self.viewer_client.set(curr_attribute_id=1)
        self._send_legend(scalars)

    def scalar_with_predicate(self, predicate):
        print("Controller: ", predicate)
        if self.sparql_client is None:
            print("No connection to server")
            return

        scalars = self.sparql_client.execute_predicate_query(predicate)
        self.viewer_client.attributes(self.sparql_client.colors, scalars)
        self.viewer_client.set(curr_attribute_id=1)
        self._send_legend(scalars)

    @report_errors_to_gui
    def connect_to_server(self, url, db_url, namespace="http://3DOntCore"):
        print("Loading all the points... ", url)
        self.gui.set_statusbar_content("Connecting to server...", 5)
        self.sparql_client = SparqlEndpoint(url, db_url, namespace="http://3DOntCore")
        print("Connected to server")
        self.gui.set_statusbar_content("Loading points from server...", 60)
        coords, colors = self.sparql_client.get_all()
        print("Points received from db")
        self.gui.set_statusbar_content("Points loaded", 5)
        self.viewer_client.load(coords, colors)
        self.viewer_client.set(point_size=0.01)
        #######################################################################################
        # self.Args.graph_uri = url
        # self.Args.ont_path = TODO
        # self.Args.pop_ont_path = TODO
        # self.Args.onto = owl2.get_ontology(self.Args.pop_ont_path).load()
        # self.Args.base = owl2.get_namespace(namespace)
        # populated_namespace = TODO
        # self.Args.populated_base = owl2.get_namespace(populated_namespace)
        # self.Args.wrapper = TODO
        # self.Args.virtuoso_isql = TODO
        #######################################################################################
        print("Point size is ", self.config.get_visualizer_pointsSize())
        self.viewer_client.set(point_size=self.config.get_visualizer_pointsSize())

    def view_point_details(self, id):
        iri = self.sparql_client.get_point_iri(id)
        details = self.sparql_client.get_node_details(iri)
        self.gui.view_node_details(details, iri)

    def view_node_details(self, iri):
        details = self.sparql_client.get_node_details(iri)
        self.gui.view_node_details(details, iri)

    @report_errors_to_gui
    def annotate_node(
        self, subject_iri, predicate_name, object_name_or_value, author_name
    ):
        onto = self.Args.onto
        predicate = getattr(onto, predicate_name)
        pop_base = self.Args.populated_base
        subject = owl2.IRIS[subject_iri[1:-1]]
        if predicate in onto.object_properties():
            obj = getattr(onto, object_name_or_value)
        smf.command_manual_annotation(self.Args, subject, predicate, obj, author_name)

    def select_all_subjects(self, predicate, object):
        colors = self.sparql_client.select_all_subjects(predicate, object)
        self.viewer_client.attributes(colors)
        self.viewer_client.set(curr_attribute_id=0)

    @report_errors_to_gui
    def tabular_query(self, query):
        result = self.sparql_client.raw_query(query)
        header = list(result.keys())
        rows = list(zip(*(result[key] for key in result)))
        self.gui.plot_tabular(header, rows)

    def _send_legend(self, scalars):
        minimum = float(min(scalars))
        maximum = float(max(scalars))
        step = (maximum - minimum) / NUMBER_OF_LABELS_IN_LEGEND
        # TODO better float format
        labels = [
            f"{minimum + step * i:.2f}" for i in range(NUMBER_OF_LABELS_IN_LEGEND)
        ]
        colors = get_color_map()
        # it's a numpy array of shape (N, 3), convert to list of hex colors
        colors = [
            "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
            for (r, g, b) in colors
        ]
        self.gui.set_legend(colors, labels)

    @report_errors_to_gui
    def configure_AWS_connection(
        self, access_key_id, secret_access_key, region, profile_name
    ):
        aws.set_aws_credentials(access_key_id, secret_access_key, region, profile_name)
        self.gui.set_statusbar_content("AWS configured for this device!", 5)

    @report_errors_to_gui
    def add_sensor(
        self,
        sensor_name,
        object_name,
        property_name,
        cert_pem_path,
        private_key_path,
        root_ca_path,
        mqtt_topic,
        client_id,
    ):
        ##### set args
        self.Args.sensor_name = sensor_name
        self.Args.object_name = object_name
        self.Args.property_name = property_name
        self.Args.cert_pem_path = cert_pem_path
        self.Args.private_key_path = private_key_path
        self.Args.root_ca_path = root_ca_path
        self.Args.mqtttopic = mqtt_topic
        self.Args.client_id = client_id
        self.gui.set_statusbar_content("Adding Sensor...", 5)
        #####execute function
        smf.command_add_sensor(self.Args)
        self.gui.set_statusbar_content("Sensor Added!", 5)
        ##### update onto
        self.Args.onto = owl2.get_ontology(self.Args.ont_path).load()
        self.gui.set_statusbar_content("Ontology Updated!", 5)
        self.gui.set_statusbar_content(
            "You can add other sensors or update their value, but refresh server connection to see it in the viewer",
            5,
        )

    @report_errors_to_gui
    def update_sensors_and_reason(self):
        self.gui.set_statusbar_content("Updating all Sensors and Reasoning...", 5)
        smf.command_update_sensors_and_reason(self.Args)
        self.gui.set_statusbar_content("Sensors Updated, Reasoning executed!", 5)
        ##### update onto
        self.Args.onto = owl2.get_ontology(self.Args.ont_path).load()
        self.gui.set_statusbar_content("Ontology Updated!", 5)
        self.gui.set_statusbar_content(
            "You can add other sensors or update their value, but refresh server connection to see it in the viewer",
            5,
        )

    ##### ONLY FOR DEBUGGING, UNTIL REAL ARG SETTING IS PREPARED IN "CONNECT TO SERVER" METHOD
    @report_errors_to_gui
    def provisional_set_args(
        self,
        graph_uri,
        ont_path,
        pop_ont_path,
        namespace,
        populated_namespace,
        virtuoso_isql,
    ):

        self.Args.graph_uri = graph_uri
        self.Args.ont_path = ont_path
        self.Args.pop_ont_path = pop_ont_path
        self.Args.onto = owl2.get_ontology(self.Args.pop_ont_path).load()
        self.Args.base = owl2.get_namespace(namespace)
        self.Args.populated_base = owl2.get_namespace(populated_namespace)
        self.Args.virtuoso_isql = virtuoso_isql
        import SPARQLWrapper

        wrapper = SPARQLWrapper.Wrapper.SPARQLWrapper(
            endpoint="http://localhost:8890/sparql"
        )
        wrapper.setReturnFormat("csv")
        wrapper.setCredentials("dba", "dba")
        self.Args.wrapper = wrapper
        self.gui.set_statusbar_content("Args configured!", 5)

    def natural_language_query(self, nl_query):
        print("Natural language query: ", nl_query)
        onto_path = self.project.get_onto_path()
        openai_client = init_client()  # TODO understand if can be done only once
        query = nl_2_sparql(
            nl_query,
            onto_path,
            self.project.get_graphNamespace(),
            self.project.get_graphUri(),
            openai_client,
            self.gui,
        )
        query = "\n".join(query)
        result, query_type = self.sparql_client.autodetect_query_nl(query)
        if query_type == "tabular":
            header = list(result.keys())
            rows = list(zip(*(result[key] for key in result)))
            self.gui.plot_tabular(header, rows)
        elif query_type == "scalar":
            self.viewer_client.attributes(self.sparql_client.colors, result)
            self.viewer_client.set(curr_attribute_id=1)
            self._send_legend(result)
        elif query_type == "select":
            self.viewer_client.attributes(result)
            self.viewer_client.set(curr_attribute_id=0)
        else:
            print(
                "Error, unknown query type: ", query_type
            )  # TODO remove, shouldn't happen

    def update_project_list(self):
        lst = Project.get_project_list()
        self.gui.set_project_list(lst)

    def open_project(self, project_name):
        print("Opening project: ", project_name)
        self.project = Project(project_name)
        self.app_state.set_projectName(self.project.get_name())
        self.gui.set_statusbar_content(f"Opened project: {project_name}", 5)
        self.connect_to_server(
            self.project.get_graphUri(),
            self.project.get_graphNamespace(),
        )

    def create_project(self, project_name, db_url, graph_uri, graph_namespace):
        print("Creating project: ", project_name)
        if Project.exists(project_name):
            # TODO use proper error handling in GUI
            self.gui.set_query_error(f"Project '{project_name}' already exists!")
            return

        self.project = Project(project_name)
        self.project.set_name(project_name)
        self.project.set_dbUrl(db_url)
        self.project.set_graphUri(graph_uri)
        self.project.set_graphNamespace(graph_namespace)
        self.project.save()
        self.gui.set_statusbar_content(f"Created project: {project_name}", 5)
        self.open_project(project_name)  # maybe remove this

    def set_color_scale(self, low, high):
        self.viewer_client.color_map("jet", (low, high))
