from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from platformdirs import user_config_dir, user_data_dir
import json
import configparser

__all__ = ["Config", "AppState"]

CONFIG_FILE = "config.ini"
STATE_FILE = "state.json"

DEFAULT_CONFIG = {
    "visualization": {
        "points_size": 0.01,
        "scalar_color_scheme": "jet",
        "highlight_color": "#FF0000",
    },
    "general": {
    },
}

DEFAULT_STATE = {
    "last_opened_file": "",
    "last_server_url": "",
    "last_namespace": "",
    "last_query": "",
    "show_legend": True,
}

CONFIG_SCHEMA = {
    "visualization": {
        "points_size": float,
        "scalar_color_scheme": str,
        "highlight_color": str,
    },
    "general": {
    },
}

STATE_SCHEMA = {
    "last_opened_file": str,
    "last_server_url": str,
    "last_namespace": str,
    "last_query": str,
    "show_legend": bool,
}

class AbstractConfig(ABC):
    def __init__(self, file_path: Path, default_config: dict, config_schema: dict):
        self.file_path = file_path
        self.config = default_config
        self.load()
        self.schema = config_schema

    @abstractmethod
    def write_config_to_file(self, file):
        pass

    @abstractmethod
    def read_config_from_file(self, file):
        pass

    def load(self):
        if self.file_path.exists():
            with open(self.file_path, 'r') as file:
                self.config = self.read_config_from_file(file)
        else:
            # keep default config and write it
            self.save()


    def save(self):
        with open(self.file_path, 'w') as file:
            self.write_config_to_file(file)

    def _validate_config_path(self, path):
        # use config schema, path is a list of strings
        current = self.schema
        for part in path:
            if part not in current:
                raise KeyError(f"Invalid configuration path: {'/'.join(path)}")
            current = current[part]
        return current # type of the last part in the path

    def _set_config_value(self, attr, value, expected_type):
        path = attr.split('_')
        if not isinstance(value, expected_type):
            raise TypeError(f"Expected type {expected_type.__name__} for '{attr}', got {type(value).__name__}")
        current = self.config
        for part in path[:-1]:
            current = current.setdefault(part, {})
        current[path[-1]] = value

    def _get_config_value(self, attr):
        path = attr.split('_')
        current = self.config
        for part in path:
            current = current[part]
        return current

    def _build_get_config(self, attr):
        path = attr.split('_')
        try:
            self._validate_config_path(path)
            return partial(self._get_config_value, attr)
        except KeyError:
            raise AttributeError(f"Configuration attribute '{attr}' not found.")

    def _build_set_config(self, attr):
        path = attr.split('_')
        try:
            expected_type = self._validate_config_path(path)
            return partial(self._set_config_value, attr, expected_type=expected_type)
        except KeyError:
            raise AttributeError(f"Configuration attribute '{attr}' not found.")

    def __getattr__(self, item):
        if item.startswith('get'):
            attr = item[3:].lower()
            return self._build_get_config(attr)
        elif item.startswith('set'):
            attr = item[3:].lower()
            return self._build_set_config(attr)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")


class Config(AbstractConfig):
    def __init__(self, app_name: str = "threedont"):
        self.config_path = Path(user_config_dir(app_name)) / CONFIG_FILE
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(self.config_path, DEFAULT_CONFIG, CONFIG_SCHEMA)

    def write_config_to_file(self, file):
        config = configparser.ConfigParser()
        for section, options in self.config.items():
            config[section] = options
        config.write(file)

    def read_config_from_file(self, file):
        config = configparser.ConfigParser()
        config.read_file(file)
        return {section: dict(config[section]) for section in config.sections()}

class AppState(AbstractConfig):
    def __init__(self, app_name: str = "threedont"):
        self.state_path = Path(user_data_dir(app_name)) / STATE_FILE
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(self.state_path, DEFAULT_STATE, STATE_SCHEMA)
        self.load()

    def write_config_to_file(self, file):
        json.dump(self.config, file, indent=2)

    def read_config_from_file(self, file):
        return json.load(file)