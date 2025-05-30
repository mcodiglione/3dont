from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from copy import deepcopy


class AbstractConfig(ABC):
    def __init__(self, file_path: Path, default_config: dict, config_schema: dict, auto_save: bool = False):
        self.file_path = file_path
        self.config = deepcopy(default_config)
        self.load()
        self.update_config_with_default(default_config)
        self.save()
        self.schema = config_schema
        self.auto_save = auto_save

    """
    When adding a config value to the application we want to add it in the existing config file
    """
    def update_config_with_default(self, default_config: dict, config = None):
        if config is None:
            config = self.config
        for key, value in default_config.items():
            if key not in config:
                self.config[key] = deepcopy(value)
            else:
                if isinstance(value, dict):
                    self.update_config_with_default(value, config[key])

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
        if self.auto_save:
            self.save()

    def _get_config_value(self, attr, field_type):
        path = attr.split('_')
        current = self.config
        for part in path:
            current = current[part]
        return field_type(current)

    def _build_get_config(self, attr):
        path = attr.split('_')
        try:
            field_type = self._validate_config_path(path)
            return partial(self._get_config_value, attr, field_type=field_type)
        except KeyError:
            raise AttributeError(f"Configuration attribute '{attr}' not found.")

    def _build_set_config(self, attr):
        path = attr.split('_')
        try:
            expected_type = self._validate_config_path(path)
            return partial(self._set_config_value, attr, expected_type=expected_type)
        except KeyError:
            raise AttributeError(f"Configuration attribute '{attr}' not found.")

    """
    Dynamically create getter and setter methods for configuration attributes.
    """
    def __getattr__(self, item):
        if item.startswith('get_'):
            attr = item[4:]
            return self._build_get_config(attr)
        elif item.startswith('set_'):
            attr = item[4:]
            return self._build_set_config(attr)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")
