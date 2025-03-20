from multiprocessing import Process, Pipe
import signal

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
    def __init__(self, commands_pipe):
        self.commands_pipe = commands_pipe

    def __getattr__(self, item):
        # check if controller has the function
        if not hasattr(Controller, item) or not callable(getattr(Controller, item)):
            raise AttributeError(f"Controller has no method {item}")

        f = lambda *args: self.commands_pipe.send((item, args))
        return f

def run_gui(port_number_pipe, commands_pipe):
    action_controller = ActionController(commands_pipe)
    gui = GuiWrapper(action_controller)
    tcp_server_port = gui.get_viewer_server_port()
    port_number_pipe.send(tcp_server_port)
    port_number_pipe.close()

    print("Running GUI")
    gui.run()
    commands_pipe.close()
    print("GUI run() exited")

class Controller:
    def __init__(self):
        port_number_receiver, port_number_sender = Pipe(duplex=False)
        commands_receiver, commands_sender = Pipe(duplex=False)
        self.commands_pipe = commands_receiver
        self.gui_process = Process(target=run_gui, args=(port_number_sender, commands_sender), daemon=True)
        self.gui_process.start()

        tcp_server_port = port_number_receiver.recv()
        self.viewer_client = Viewer(tcp_server_port)
        self.sparql_client = None

    def stop(self):
        print("Stopping application...")
        self.gui_process.terminate()
        self.gui_process.join()

    def run(self):
        def signal_handler(sig, frame):
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print("Running controller")
        while True:
            try:
                command = self.commands_pipe.recv()
            except EOFError:
                # raised when the pipe is closed
                break
            function_name, args = command
            getattr(self, function_name)(*args)

    def execute_query(self, query):
        print("Controller: ", query)
        if self.sparql_client is None:
            print("No connection to server")
            return

        colors = self.sparql_client.execute_select_query(query)
        self.viewer_client.attributes(colors)

    def connect_to_server(self, url):
        """
        ?p urban:Constitutes ?part.
        ?part urban:Is_part_of ?obj.
        ?obj a urban:Type_Building.
        """
        print("Loading all the points... ", url)
        self.sparql_client = SparqlEndpoint(url)
        print("Connected to server")
        coords, colors = self.sparql_client.get_all()
        print("Points received from db")
        self.viewer_client.load(coords, colors)
        self.viewer_client.set(point_size=0.01)