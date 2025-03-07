from concurrent.futures import ThreadPoolExecutor
import numpy as np
import functools

from .viewer import Viewer
from ..gui import GuiWrapper

__all__ = ['Controller']

# Create a global executor
executor = ThreadPoolExecutor()

# Define the decorator
def run_async(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        future = executor.submit(func, self, *args, **kwargs)
        # Handle errors or result in a callback after the function is done
        def handle_result(future):
            if future.exception():
                print(f"Error in {func.__name__}: {future.exception()}")
            else:
                print(f"{func.__name__} completed successfully")
        future.add_done_callback(handle_result)
    return wrapper

class Controller:
    def __init__(self):
        self.gui = GuiWrapper(self)
        self.viewerClient = Viewer(self.gui.get_viewer_server_port())

    def stop(self):
        print("Stopping application...")
        self.gui.stop()

    def run(self):
        self.gui.run()


    @run_async
    def execute_query(self, query):
        print("Controller: ", query)
        # TODO

    @run_async
    def connect_to_server(self, url):
        print("Sending points...")
        xyz = np.random.rand(100000, 3)
        self.viewerClient.load(xyz)
        self.viewerClient.attributes(xyz)
        # TODO
