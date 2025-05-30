import logging
import sys
from queue import Queue
from urllib.error import URLError

from SPARQLWrapper.SPARQLExceptions import QueryBadFormed

from .db import SparqlEndpoint, WrongResultFormatException, EmptyResultSetException
from .viewer import Viewer, get_color_map
from ..gui import GuiWrapper
from .state import Project

__all__ = ['Controller']

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
            response = str(e).split('Response:\n')[1]
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
        self.project = None

    def stop(self):
        print("Stopping controller...")
        self.commands_queue.put(None)

    def run(self):
        # this will create a thread that runs `run_event_loop`
        self.gui.run()

    def run_event_loop(self):
        print("Running controller")
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
                logging.exception("Error in controller running function %s", function_name)

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
    def connect_to_server(self, graph_url, namespace):
        print("Loading all the points... ", graph_url)
        self.gui.set_statusbar_content("Connecting to server...", 5)
        # TODO handle graph_url in GUI
        self.sparql_client = SparqlEndpoint(graph_url, graph_url,  namespace)
        print("Connected to server")
        self.gui.set_statusbar_content("Loading points from server...", 60)
        coords, colors = self.sparql_client.get_all()
        print("Points received from db")
        self.gui.set_statusbar_content("Points loaded", 5)
        self.viewer_client.load(coords, colors)
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
    def annotate_node(self, iri, predicate, value):
        print("Controller: ", iri, predicate, value)
        if self.sparql_client is None:
            print("No connection to server")
            return

        self.sparql_client.annotate_node(iri, predicate, value)

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
        labels = [f"{minimum + step * i:.2f}" for i in range(NUMBER_OF_LABELS_IN_LEGEND)]
        colors = get_color_map()
        # it's a numpy array of shape (N, 3), convert to list of hex colors
        colors = ["#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255)) for (r, g, b) in colors]
        self.gui.set_legend(colors, labels)

    @report_errors_to_gui
    def natural_language_query(self, query):
        print("Natural language query: ", query)
        # TODO
        self.gui.set_query_error("Natural language query not implemented yet!")

    def get_project_list(self):
        lst =  Project.get_project_list()
        self.gui.set_project_list(lst)

    def open_project(self, project_name):
        print("Opening project: ", project_name)
        self.project = Project(project_name)
        self.app_state.set_projectName(self.project.get_name())
        self.gui.set_statusbar_content(f"Opened project: {project_name}", 5)
        self.connect_to_server(self.project.get_dbUrl(), self.project.get_graphNamespace())

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
        self.app_state.set_project(self.project.get_name())
        self.gui.set_statusbar_content(f"Created project: {project_name}", 5)
        self.open_project(project_name) # maybe remove this
