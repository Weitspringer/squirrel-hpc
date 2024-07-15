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
        conf_dict = self.conf["local"]
        result = {}
        for key, value in conf_dict.items():
            result.update({key: Path(value)})
        return result

    def get_influx_config(self) -> dict:
        """Get all options relevant to InfluxDB."""
        conf_dict = self.conf["influxdb"]
        return {
            "url": conf_dict["url"],
            "org": conf_dict["org"],
            "token": conf_dict["token"],
        }

    def get_builtin_forecast_config(self) -> dict:
        """Options for builtin forecasting."""
        conf_dict = self.conf["builtin.forecast"]
        return {
            "forecast_days": int(conf_dict["forecast_days"]),
            "lookback_days": int(conf_dict["lookback_days"]),
        }


Config = SquirrelConfig()
