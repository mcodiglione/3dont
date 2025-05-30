from platformdirs import user_data_dir
from pathlib import Path
import json

from .abstract_config import AbstractConfig

STATE_FILE = "state.json"

DEFAULT_STATE = {
    "lastOpenedFile": "",
    "lastServerUrl": "",
    "lastNamespace": "",
    "lastQuery": "",
    "showLegend": True,
    "projectName": "",
}

STATE_SCHEMA = {
    "lastOpenedFile": str,
    "lastServerUrl": str,
    "lastNamespace": str,
    "lastQuery": str,
    "showLegend": bool,
    "projectName": str,
}

class AppState(AbstractConfig):
    def __init__(self, app_name: str = "threedont"):
        self.state_path = Path(user_data_dir(app_name)) / STATE_FILE
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(self.state_path, DEFAULT_STATE, STATE_SCHEMA, auto_save=True)
        self.load()

    def write_config_to_file(self, file):
        json.dump(self.config, file, indent=2)

    def read_config_from_file(self, file):
        return json.load(file)