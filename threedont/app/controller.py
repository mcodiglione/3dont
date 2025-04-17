from queue import Queue
import sys

from .viewer import Viewer
from .db import SparqlEndpoint
from ..gui import GuiWrapper

__all__ = ['Controller']

"""
    The commands_pipe will transport function calls from the GUI to the Controller.
    A functions here is a tuple of the form (function_name, args).
    ActionController is just a middleman to help with the transport between the processes, a facade.
"""

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

class Controller:
    def __init__(self):
        self.commands_queue = Queue()
        action_controller = ActionController(self.commands_queue, self.run_event_loop)
        self.gui = GuiWrapper(action_controller, sys.argv)
        viewer_server_port = self.gui.get_viewer_server_port()
        self.viewer_client = Viewer(viewer_server_port)
        self.sparql_client = None

    def stop(self):
        print("Stopping controller...")
        self.commands_queue.put(None)


    def run(self):
        # this will create a thread that runs `run_event_loop`
        self.gui.run()

    def run_event_loop(self):
        print("Running controller")
        command = self.commands_queue.get()
        while command is not None:
            function_name, args = command
            getattr(self, function_name)(*args)

            command = self.commands_queue.get()

    def execute_query(self, query):
        print("Controller: ", query)
        if self.sparql_client is None:
            print("No connection to server")
            return

        colors = self.sparql_client.execute_select_query(query)
        self.viewer_client.attributes(colors)

    def connect_to_server(self, url, namespace):
        """
        ?p urban:Constitutes ?part.
        ?part urban:Is_part_of ?obj.
        ?obj a urban:Type_Building.
        """
        print("Loading all the points... ", url)
        self.gui.set_statusbar_content("Connecting to server...", 5)
        self.sparql_client = SparqlEndpoint(url, namespace)
        print("Connected to server")
        self.gui.set_statusbar_content("Loading points from server...", 20)
        coords, colors = self.sparql_client.get_all()
        print("Points received from db")
        self.gui.set_statusbar_content("Points loaded", 5)
        self.viewer_client.load(coords, colors)
        self.viewer_client.set(point_size=0.01)

    def view_point_details(self, id):
        iri = self.sparql_client.get_point_iri(id)
        details = self.sparql_client.get_node_details(iri)
        self.gui.view_node_details(details, iri)

    def view_node_details(self, iri):
        details = self.sparql_client.get_node_details(iri)
        self.gui.view_node_details(details, iri)