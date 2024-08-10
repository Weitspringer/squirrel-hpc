from datetime import datetime, UTC
from pathlib import Path

import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import _write_data_from_df


def ingest_emaps_history(path_to_csv: Path):
    influx_opt = Config.get_influx_config()["gci"]["history"]
    emaps_df = pd.read_csv(path_to_csv)
    relevant_data = emaps_df[
        ["Zone Id", "Carbon Intensity gCO₂eq/kWh (LCA)", "Datetime (UTC)"]
    ]
    df_mapped = relevant_data.rename(
        columns={
            "Zone Id": "zone",
            "Carbon Intensity gCO₂eq/kWh (LCA)": "gci",
            "Datetime (UTC)": "time",
        }
    )
    zone_ids = df_mapped["zone"].unique()
    assert len(zone_ids) == 1
    influx_opt.get("tags").update({"zone": zone_ids[0]})
    df_mapped.loc[:, "time"] = df_mapped["time"].apply(lambda x: _transform_datestr(x))
    _write_data_from_df(
        data=df_mapped, options=influx_opt, value_column="gci", time_column="time"
    )


def _transform_datestr(datestr: str):
    x_dt = datetime.fromisoformat(datestr)
    x_dt = x_dt.astimezone(tz=UTC)
    return x_dt.isoformat(timespec="microseconds")
