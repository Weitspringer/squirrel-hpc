"""Analyze statistical properties of GCI history from different zones."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data
from src.sim.common.pipeline import adjust_plot_font

ZONE_LABELS = {
    "AU-NSW": "Australia NSW",
    "CA-ON": "Ontario",
    "CA-QC": "Québec",
    "DE": "Germany",
    "DK": "Denmark",
    "FR": "France",
    "GB": "Great Britain",
    "IN-WE": "West India",
    "IS": "Iceland",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "SE": "Sweden",
    "TW": "Taiwan",
    "US-MIDA-PJM": "USA (PJM)",
    "ZA": "South Africa",
}
YEAR = "2023"
RESULT_DIR = Path("viz") / "misc"
RESULT_DIR.mkdir(exist_ok=True, parents=True)
plt.style.use("seaborn-v0_8")


def analyze(zones: list[str]) -> None:
    stats = []
    adjust_plot_font()
    for zone in zones:
        start = datetime.fromisoformat(f"{YEAR}-01-01T00:00:00+00:00")
        end = datetime.fromisoformat(f"{YEAR}-12-31T23:59:59+00:00")
        influx_options = Config.get_influx_config()["gci"]["history"]
        influx_options.get("tags").update({"zone": zone})
        gci_hist = get_gci_data(start=start, stop=end, options=influx_options)
        gci_hist["Month"] = gci_hist["time"].apply(lambda x: x.month)
        gci_hist = gci_hist.set_index("time")
        day_cvs = []
        day_avg = []
        try:
            gci_daily = np.asarray(gci_hist["gci"].tolist()).reshape((365, 24))
            for gci_day in gci_daily:
                day_avg.append(np.mean(gci_hist))
                day_cvs.append(np.std(gci_day) / np.mean(gci_day))
        except ValueError:
            print(f"Zone has not enough data: {zone}")
            continue
        avg_annually = np.mean(gci_hist["gci"])
        cv_annually = np.std(gci_hist["gci"]) / np.mean(gci_hist["gci"])
        avg_daily = np.median(day_avg)
        cv_daily = np.median(day_cvs)
        # Write stats
        stats.append(
            {
                "zone": zone,
                "gci_average_anually": avg_annually,
                "gci_average_daily": avg_daily,
                "gci_cv_anually": cv_annually,
                "gci_cv_daily": cv_daily,
                "num_points": len(gci_hist),
            }
        )
    stat_df = pd.DataFrame(stats)
    stat_df.set_index("zone", inplace=True)
    cm = plt.get_cmap("tab20")
    ax = plt.gca()
    ax.set_prop_cycle(color=[cm(1.0 * i / len(zones)) for i in range(len(zones))])
    for zone, stat in stat_df.iterrows():
        plt.plot(
            stat["gci_average_anually"],
            stat["gci_cv_anually"],
            "o",
            label=ZONE_LABELS[zone],
            markersize=10,
        )
    plt.title("[Annually] Properties of GCI, 2023")
    plt.xlabel("Average [gCO2e/kWh]")
    plt.ylabel("Coefficient of Variation")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout(pad=1)
    plt.savefig(RESULT_DIR / "gci_in_zones_annually.pdf")
    plt.clf()
    cm = plt.get_cmap("tab20")
    ax = plt.gca()
    ax.set_prop_cycle(color=[cm(1.0 * i / len(zones)) for i in range(len(zones))])
    for zone, stat in stat_df.iterrows():
        plt.plot(
            stat["gci_average_daily"],
            stat["gci_cv_daily"],
            "o",
            label=ZONE_LABELS[zone],
            markersize=10,
        )
    plt.title("[Daily] Properties of GCI, 2023")
    plt.xlabel("Average [gCO2e/kWh]")
    plt.ylabel("Coefficient of Variation")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout(pad=1)
    plt.savefig(RESULT_DIR / "gci_in_zones_daily.pdf")
    # Write stats
    stat_df.to_csv(RESULT_DIR / "gci_in_zones_stats.csv")


if __name__ == "__main__":
    analyze(ZONE_LABELS.keys())
