"""Interface for InfluxDB"""

from datetime import datetime, UTC

from influxdb_client import InfluxDBClient


def get_gci_data(url: str, token: str, org: str, start: datetime, stop: datetime):
    """Get GCI data from InfluxDB"""
    client = InfluxDBClient(url=url, token=token, org=org)
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
    gci_data = client.query_api().query_data_frame(query=query, org=org)
    gci_data = gci_data[["_time", "g_co2eq_per_kWh"]].rename(
        columns={"_time": "time", "g_co2eq_per_kWh": "gci"}
    )
    return gci_data
