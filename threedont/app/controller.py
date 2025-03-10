from multiprocessing import Process, Pipe
import numpy as np
import signal

from .viewer import Viewer
from ..gui import GuiWrapper

__all__ = ['Controller']

"""
    The commands_pipe will transport function calls from the GUI to the Controller.
    A functions here is a tuple of the form (function_name, args).
    ActionController is just a middleman to help with the transport between the processes, a facade.
"""

# Thi
class ActionController:
    def __init__(self, commands_pipe):
        self.commands_pipe = commands_pipe

    def execute_query(self, query):
        self.commands_pipe.send(('execute_query', (query,)))

    def connect_to_server(self, url):
        self.commands_pipe.send(('connect_to_server', (url,)))

def run_gui(portNumberPipe, commands_pipe):
    action_controller = ActionController(commands_pipe)
    gui = GuiWrapper(action_controller)
    tcp_server_port = gui.get_viewer_server_port()
    portNumberPipe.send(tcp_server_port)
    portNumberPipe.close()

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
        self.viewerClient = Viewer(tcp_server_port)

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
        # TODO

    def connect_to_server(self, url):
        print("Sending points... ", url)
        xyz = np.random.rand(10000, 3)
        self.viewerClient.load(xyz, xyz)
        self.viewerClient.set(point_size=0.005)
        # TODO