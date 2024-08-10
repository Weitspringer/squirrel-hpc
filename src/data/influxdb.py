"""Interface for InfluxDB"""

from datetime import datetime, UTC

from influxdb_client import InfluxDBClient
import pandas as pd

from src.config.squirrel_conf import Config

INFLUX_OPT = Config.get_influx_config()


def get_gci_data(start: datetime, stop: datetime) -> pd.DataFrame:
    """Get GCI data from InfluxDB."""
    client = _get_client()
    start = start.astimezone(tz=UTC)
    stop = stop.astimezone(tz=UTC)
    options = INFLUX_OPT["gci"]["history"]
    query = f"""
    from(bucket: "{options["bucket"]}")
    |> range(start: {start.strftime("%Y-%m-%dT%H:%M:%SZ")}, stop: {stop.strftime("%Y-%m-%dT%H:%M:%SZ")})
    |> filter(fn: (r) => r["_measurement"] == "{options["measurement"]}")
    |> filter(fn: (r) => r["_field"] == "{options["field"]}")
    """
    tags = options["tags"]
    for tag, tag_value in tags.items():
        query += f"""|> filter(fn: (r) => r["{tag}"] == "{tag_value}")\n"""
    query += (
        """|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")"""
    )
    gci_data = client.query_api().query_data_frame(query=query, org=INFLUX_OPT["org"])
    if len(gci_data) > 0:
        gci_data = gci_data[["_time", options["field"]]].rename(
            columns={"_time": "time", options["field"]: "gci"}
        )
    else:
        raise ValueError("No GCI data available.")
    return gci_data


def write_gci_forecast(forecast: pd.DataFrame) -> None:
    """Write GCI forecast to InfluxDB.
    Forecast dataframe is required to have 'time' and 'gci' columns.
    """
    client = _get_client()
    options = INFLUX_OPT["gci"]["forecast"]
    bucket = options["bucket"]
    measurement = options["measurement"]
    field = options["field"]
    with client.write_api() as writer:
        for _, row in forecast.iterrows():
            record = {
                "measurement": measurement,
                "fields": {field: row["gci"]},
                "tags": options["tags"],
                "time": row["time"],
            }
            writer.write(bucket=bucket, record=record)


def _get_client() -> InfluxDBClient:
    return InfluxDBClient(
        url=INFLUX_OPT["url"], token=INFLUX_OPT["token"], org=INFLUX_OPT["org"]
    )
