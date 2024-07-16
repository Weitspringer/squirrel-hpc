"""Configuration for Squirrel."""

import configparser
from pathlib import Path


class SquirrelConfig:
    """This class reads the config.ini file"""

    def __init__(self, path):
        self.conf = self._read_config(path)

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

    def get_forecast_days(self) -> int:
        """Get amount of days for the forecast."""
        return int(self.conf.get("forecast", "forecast_days"))

    def get_builtin_forecast_config(self) -> dict:
        """Options for builtin forecasting."""
        fc = self.conf.get("forecast", "forecast_days")
        lb = self.conf.get("forecast.builtin", "lookback_days")
        return {
            "forecast_days": int(fc),
            "lookback_days": int(lb),
        }


Config = SquirrelConfig(path="squirrel.ini")
