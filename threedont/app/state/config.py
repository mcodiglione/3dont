from platformdirs import user_config_dir
from pathlib import Path
import configparser

from .abstract_config import AbstractConfig


CONFIG_FILE = "config.ini"

DEFAULT_CONFIG = {
    "visualizer": {
        "pointsSize": 0.01,
        "scalarColorScheme": "jet",
        "highlightColor": "#FF0000",
    },
    "general": {
        "loadLastProject": True,
    },
}

CONFIG_SCHEMA = {
    "visualizer": {
        "pointsSize": float,
        "scalarColorScheme": str,
        "highlightColor": str,
    },
    "general": {
        "loadLastProject": bool,
    },
}

class Config(AbstractConfig):
    def __init__(self, app_name: str = "threedont"):
        self.config_path = Path(user_config_dir(app_name)) / CONFIG_FILE
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(self.config_path, DEFAULT_CONFIG, CONFIG_SCHEMA, auto_save=False)

    def write_config_to_file(self, file):
        config = configparser.ConfigParser()
        for section, options in self.config.items():
            config[section] = {k: str(v) for k, v in options.items()}
        config.write(file)

    """
    Ini makes everything lowercase, so we need to convert it back to camel case
    """
    def _to_camel_case(self, lower_str, options):
        for option in options:
            if lower_str == option.lower():
                return option

    def read_config_from_file(self, file):
        config = configparser.ConfigParser()
        config.read_file(file)
        result = {}
        for section in config.sections():
            section_dict = {}
            section = self._to_camel_case(section, CONFIG_SCHEMA.keys())
            for option, value in config.items(section):
                camel_case_option = self._to_camel_case(option, CONFIG_SCHEMA[section].keys())
                if CONFIG_SCHEMA[section][camel_case_option] == bool:
                    value = config[section].getboolean(option)
                section_dict[camel_case_option] = value
            result[section] = section_dict
        return result

