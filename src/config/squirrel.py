"""Configuration for Squirrel."""

import configparser
from pathlib import Path


class SquirrelConfig:
    """This class reads the config.ini file"""

    def __init__(self):
        self.conf = self._read_config("config.ini")

    def _read_config(self, config_file_path) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read(config_file_path)
        return config

    def __str__(self):
        return str(self.conf.items())

    def get_local_paths(self) -> dict:
        """Returns paths to local resources."""
        return self.conf["local"]

    def get_influx_config(self) -> dict:
        """Get all options relevant to InfluxDB."""
        return self.conf["influxdb"]

    def get_builtin_forecast_config(self) -> dict:
        """Options for builtin forecasting."""
        return self.conf.get("builtin.forecast")


Config = SquirrelConfig()
