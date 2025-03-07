from multiprocessing import Process, Queue, Pipe
import numpy as np

from .viewer import Viewer
from ..gui import GuiWrapper

__all__ = ['Controller']

"""
    The commandQueue will transport function calls from the GUI to the Controller.
    A functions here is a tuple of the form (function_name, args).
    ActionController is just a middleman to help with the transport between the processes, a facade.
"""

# Thi
class ActionController:
    def __init__(self, commandsQueue):
        self.commandsQueue = commandsQueue

    def execute_query(self, query):
        self.commandsQueue.put(('execute_query', (query,)))

    def connect_to_server(self, url):
        self.commandsQueue.put(('connect_to_server', (url,)))

def run_gui(portNumberPipe, commandsQueue):
    actionController = ActionController(commandsQueue)
    gui = GuiWrapper(actionController)
    tcp_server_port = gui.get_viewer_server_port()
    portNumberPipe.send(tcp_server_port)
    portNumberPipe.close()

    print("Running GUI")
    gui.run()
    commandsQueue.put(None)
    commandsQueue.close()
    print("GUI stopped")

class Controller:
    def __init__(self):
        portNumberPipeReceiver, portNumberPipeSender = Pipe(duplex=False)
        self.commandsQueue = Queue()
        self.gui_process = Process(target=run_gui, args=(portNumberPipeSender, self.commandsQueue))
        self.gui_process.start()

        tcp_server_port = portNumberPipeReceiver.recv()
        self.viewerClient = Viewer(tcp_server_port)

    def stop(self):
        print("Stopping application...")
        self.gui_process.terminate()
        self.gui_process.join()

    def run(self):
        print("Running controller")
        while True:
            command = self.commandsQueue.get()
            if command is None:
                break
            function_name, args = command
            getattr(self, function_name)(*args)

    def execute_query(self, query):
        print("Controller: ", query)
        # TODO

    def connect_to_server(self, url):
        print("Sending points... ", url)
        xyz = np.random.rand(100, 3)
        self.viewerClient.load(xyz, xyz)
        # TODO