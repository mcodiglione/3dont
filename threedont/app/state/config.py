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
    },
}


CONFIG_SCHEMA = {
    "visualizer": {
        "pointsSize": float,
        "scalarColorScheme": str,
        "highlightColor": str,
    },
    "general": {
    },
}

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

