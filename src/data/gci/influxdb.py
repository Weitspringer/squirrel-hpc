"""Interface for InfluxDB"""

from datetime import datetime, UTC

from influxdb_client import InfluxDBClient
import pandas as pd

from src.config.squirrel import Config

INFLUX_OPT = Config.get_influx_config()


def get_gci_trace_data(start: datetime, stop: datetime):
    """Get GCI trace from InfluxDB"""
    client = InfluxDBClient(
        url=INFLUX_OPT["url"], token=INFLUX_OPT["token"], org=INFLUX_OPT["org"]
    )
    start = start.astimezone(tz=UTC)
    stop = stop.astimezone(tz=UTC)
    query = f"""
    from(bucket: "gci_trace")
    |> range(start: {start.strftime("%Y-%m-%dT%H:%M:%SZ")}, stop: {stop.strftime("%Y-%m-%dT%H:%M:%SZ")})
    |> filter(fn: (r) => r["_measurement"] == "emaps")
    |> filter(fn: (r) => r["_field"] == "g_co2eq_per_kWh")
    |> filter(fn: (r) => r["zone"] == "DE")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    """
    gci_data = client.query_api().query_data_frame(query=query, org=INFLUX_OPT["org"])
    if len(gci_data) > 0:
        gci_data = gci_data[["_time", "g_co2eq_per_kWh"]].rename(
            columns={"_time": "time", "g_co2eq_per_kWh": "gci"}
        )
    else:
        raise ValueError("No GCI trace data for the given time available.")
    return gci_data


def get_gci_data(start: datetime, stop: datetime) -> pd.DataFrame:
    """Get GCI data from InfluxDB"""
    client = InfluxDBClient(
        url=INFLUX_OPT["url"], token=INFLUX_OPT["token"], org=INFLUX_OPT["org"]
    )
    start = start.astimezone(tz=UTC)
    stop = stop.astimezone(tz=UTC)
    query = f"""
    from(bucket: "squirrel")
    |> range(start: {start.strftime("%Y-%m-%dT%H:%M:%SZ")}, stop: {stop.strftime("%Y-%m-%dT%H:%M:%SZ")})
    |> filter(fn: (r) => r["_measurement"] == "electricity_maps")
    |> filter(fn: (r) => r["_field"] == "carbonIntensity")
    |> filter(fn: (r) => r["zone"] == "DE")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    """
    gci_data = client.query_api().query_data_frame(query=query, org=INFLUX_OPT["org"])
    if len(gci_data) > 0:
        gci_data = gci_data[["_time", "carbonIntensity"]].rename(
            columns={"_time": "time", "carbonIntensity": "gci"}
        )
    else:
        raise ValueError("No GCI data available.")
    return gci_data
