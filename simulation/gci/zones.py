"""Analyze statistical properties of GCI history from different zones."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data

ZONES = ["DE", "FR", "GB", "PL", "US-MIDA-PJM"]
YEAR = "2023"
RESULT_DIR = Path("viz") / "simulation" / "gci_zones"
RESULT_DIR.mkdir(exist_ok=True)


def analyze_zone(zone: str) -> None:
    start = datetime.fromisoformat(f"{YEAR}-01-01T00:00:00+00:00")
    end = datetime.fromisoformat(f"{YEAR}-12-31T23:59:59+00:00")
    influx_options = Config.get_influx_config()["gci"]["history"]
    influx_options.get("tags").update({"zone": zone})
    gci_hist = get_gci_data(start=start, stop=end, options=influx_options)
    gci_hist["Month"] = gci_hist["time"].apply(lambda x: x.month)
    gci_hist = gci_hist.set_index("time")
    sns.boxplot(data=gci_hist, x="Month", y="gci")


if __name__ == "__main__":
    for zone in ZONES:
        analyze_zone(zone=zone)
        plt.savefig(RESULT_DIR / f"{zone}.png")
        plt.clf()
