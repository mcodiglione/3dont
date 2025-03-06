import numpy as np

from .viewer import Viewer
from ..gui import GuiWrapper

__all__ = ['Controller']

class Controller:
    def __init__(self):
        self.gui = GuiWrapper(self)
        self.viewer = Viewer(self.gui.get_viewer_server_port())

    def stop(self):
        print("Stopping application...")
        self.gui.stop()

    def run(self):
        self.gui.run()


    def execute_query(self, query):
        print("Controller: ", query)
        # TODO

    def connect_to_server(self, url):
        xyz = np.random.rand(100, 3)
        self.viewer.load(xyz, xyz)
        # TODO