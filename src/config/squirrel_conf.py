"""Configuration for Squirrel."""

from json import loads
from pathlib import Path

from src.config.ini_conf import IniConfig


class SquirrelConfig(IniConfig):
    """Reads the squirrel config .ini file"""

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
        c_dict = {
            "url": conf_dict["url"],
            "org": conf_dict["org"],
            "token": conf_dict["token"],
            "gci": {
                "history": {
                    "bucket": hist_dict["bucket"],
                    "measurement": hist_dict["measurement"],
                    "field": hist_dict["field"],
                    "tags": loads(hist_dict["tags"]),
                },
                "forecast": {
                    "bucket": fc_dict["bucket"],
                    "measurement": fc_dict["measurement"],
                    "field": fc_dict["field"],
                    "tags": loads(fc_dict["tags"]),
                },
            },
        }
        return c_dict

    def use_builtin_forecast(self) -> bool:
        """Check if forecast should be used built-in or should be fetched."""
        return self.conf.getboolean("forecast", "use_builtin")

    def get_forecast_days(self) -> int:
        """Get amount of days for the forecast."""
        return int(self.conf.get("forecast", "forecast_days"))

    def get_lookback_days(self) -> int:
        """Get amount of lookback days for the forecast."""
        return int(self.conf.get("forecast.builtin", "lookback_days"))


Config = SquirrelConfig(
    path=Path(__file__).resolve().parent / ".." / ".." / "config" / "squirrel.cfg"
)
