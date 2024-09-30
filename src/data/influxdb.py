"""Interface for InfluxDB"""

from datetime import datetime, UTC

from influxdb_client import InfluxDBClient
import pandas as pd

from src.config.squirrel_conf import Config

INFLUX_OPT = Config.get_influx_config()


def get_gci_data(
    start: datetime, stop: datetime, options: dict | None = None
) -> pd.DataFrame:
    """Get GCI data from InfluxDB."""
    if not options:
        options = INFLUX_OPT["gci"]["history"]
    gci_data = _get_data_as_df(start=start, stop=stop, options=options)
    if len(gci_data) > 0:
        gci_data = gci_data[["_time", options["field"]]].rename(
            columns={"_time": "time", options["field"]: "gci"}
        )
    else:
        raise ValueError("No GCI data available.")
    return gci_data


def delete_data(start: datetime, stop: datetime, options: dict) -> None:
    """Delete data from InfluxDB."""
    if not options:
        return
    bucket = options.get("bucket")
    measurement = options.get("measurement")
    tags = options.get("tags")
    predicate = f'_measurement="{measurement}"'
    for key, value in tags.items():
        predicate += f' AND {key}="{value}"'
    influx_client = _get_client()
    influx_client.delete_api().delete(
        start=start, stop=stop, predicate=predicate, bucket=bucket
    )


def write_gci_forecast(forecast: pd.DataFrame, options: dict | None = None) -> None:
    """Write GCI forecast to InfluxDB.
    Forecast dataframe is required to have 'time' and 'gci' columns.
    """
    if not options:
        options = INFLUX_OPT["gci"]["forecast"]
    _write_data_from_df(
        data=forecast,
        options=options,
        value_column="gci",
        time_column="time",
    )


def _get_client() -> InfluxDBClient:
    return InfluxDBClient(
        url=INFLUX_OPT["url"], token=INFLUX_OPT["token"], org=INFLUX_OPT["org"]
    )


def _write_data_from_df(
    data: pd.DataFrame, options: dict, value_column: str, time_column: str
) -> None:
    client = _get_client()
    with client.write_api() as writer:
        for _, row in data.iterrows():
            record = {
                "measurement": options["measurement"],
                "fields": {options["field"]: row[value_column]},
                "tags": options["tags"],
                "time": row[time_column],
            }
            writer.write(bucket=options["bucket"], record=record)


def _get_data_as_df(start: datetime, stop: datetime, options: dict) -> pd.DataFrame:
    client = _get_client()
    start = start.astimezone(tz=UTC)
    stop = stop.astimezone(tz=UTC)
    query = f"""
    from(bucket: "{options["bucket"]}")
    |> range(start: {start.strftime("%Y-%m-%dT%H:%M:%SZ")}, stop: {stop.strftime("%Y-%m-%dT%H:%M:%SZ")})
    |> filter(fn: (r) => r["_measurement"] == "{options["measurement"]}")
    |> filter(fn: (r) => r["_field"] == "{options["field"]}")
    """
    for tag, tag_value in options["tags"].items():
        query += f"""|> filter(fn: (r) => r["{tag}"] == "{tag_value}")\n"""
    query += (
        """|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")"""
    )
    return client.query_api().query_data_frame(query=query)
