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
        hist_dict = self.conf["influxdb.gci.history"]
        fc_dict = self.conf["influxdb.gci.forecast"]
        return {
            "url": conf_dict["url"],
            "org": conf_dict["org"],
            "token": conf_dict["token"],
            "gci": {
                "history": {
                    "bucket": hist_dict["bucket"],
                    "measurement": hist_dict["measurement"],
                    "field": hist_dict["field"],
                    "zone": hist_dict["zone"],
                },
                "forecast": {
                    "bucket": fc_dict["bucket"],
                    "measurement": fc_dict["measurement"],
                    "field": fc_dict["field"],
                    "zone": fc_dict["zone"],
                },
            },
        }

    def get_forecast_days(self) -> int:
        """Get amount of days for the forecast."""
        return int(self.conf.get("forecast", "forecast_days"))

    def get_lookback_days(self) -> int:
        """Get amount of lookback days for the forecast."""
        return int(self.conf.get("forecast.builtin", "lookback_days"))


Config = SquirrelConfig(path="squirrel.ini")
