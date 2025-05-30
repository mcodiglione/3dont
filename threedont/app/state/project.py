from platformdirs import user_data_dir
from pathlib import Path
import json
import re
import unicodedata

from .abstract_config import AbstractConfig

PROJECT_FILE = "project.json"

DEFAULT_PROJECT_CONFIG = {
    "name": "",
    "graphUri": "",
    "graphNamespace": "",
    "dbUrl": "",
}

PROJECT_SCHEMA = {
    "name": str,
    "graphUri": str,
    "graphNamespace": str,
    "dbUrl": str,
}


def safe_filename(input_string, replacement='_', max_length=255):
    normalized = unicodedata.normalize('NFKD', input_string).encode('ascii', 'ignore').decode()
    # Replace invalid characters with the replacement
    safe = re.sub(r'[^a-zA-Z0-9._-]', replacement, normalized)
    safe = re.sub(f'{re.escape(replacement)}+', replacement, safe).strip(replacement)
    return safe[:max_length]


class Project(AbstractConfig):
    def __init__(self, project_name):
        self.project_path = Path(user_data_dir("threedont")) / "projects" / f"{safe_filename(project_name)}"
        self.project_path.mkdir(parents=True, exist_ok=True)
        super().__init__(self.project_path / PROJECT_FILE, DEFAULT_PROJECT_CONFIG, PROJECT_SCHEMA)

    def write_config_to_file(self, file):
        json.dump(self.config, file, indent=2)

    def read_config_from_file(self, file):
        return json.load(file)