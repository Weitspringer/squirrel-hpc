"""Configuration using an .ini file."""

import configparser
from pathlib import Path


class IniConfig:
    """Configuration using an .ini file."""

    def __init__(self, path: Path):
        self.conf = self._read_config(path)

    def _read_config(self, config_file_path: Path) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read(config_file_path)
        return config

    def __str__(self):
        return str(self.conf.items())
