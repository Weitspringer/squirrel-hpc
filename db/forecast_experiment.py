from datetime import datetime, timedelta, UTC

from influxdb_client import InfluxDBClient
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

TOKEN = ""
BUCKET = ""
FIELD = ""
ORG = ""
URL = ""

TOTAL_DAYS = 30
FORECAST_DAYS = 1
LOOKBACK_DAYS = 2


if __name__ == "__main__":
    client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)

    start_point = datetime.now(tz=UTC)
    start_point = start_point - timedelta(
        hours=start_point.hour % 24,
        minutes=start_point.minute,
        seconds=start_point.second,
        microseconds=start_point.microsecond,
    )

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -{TOTAL_DAYS}d)
    |> filter(fn: (r) => r["_measurement"] == "emaps")
    |> filter(fn: (r) => r["_field"] == "{FIELD}")
    |> filter(fn: (r) => r["zone"] == "DE")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    """

    gci_data = client.query_api().query_data_frame(query=query, org=ORG)
    # Initialize forecasting data
    all_forecasts = pd.DataFrame()
    rmse_values = []

    # 24 hour forecasts for the whole time range
    for i in range(TOTAL_DAYS - LOOKBACK_DAYS):
        break_point = pd.to_datetime(
            start_point - timedelta(days=FORECAST_DAYS * i), utc=True, unit="ns"
        )
        lookback_point = pd.to_datetime(
            break_point - timedelta(days=LOOKBACK_DAYS), utc=True, unit="ns"
        )
        gci_hist = gci_data[gci_data["_time"] < break_point]
        window = gci_hist[gci_hist["_time"] >= lookback_point]
        # Apply test when possible
        # if i > 0:
        #    gci_test = gci_data[gci_data["_time"] >= break_point]
        forecast_times = pd.date_range(
            start=break_point,
            periods=FORECAST_DAYS * 24,
            freq="h",
            tz="UTC",
        )
        day_ahead_forecast = []
        for time_point in forecast_times:
            points = []
            for day_offset in range(1, LOOKBACK_DAYS + 1):
                past_time_point = time_point - timedelta(days=day_offset)
                points.append(
                    window[window["_time"] == past_time_point][FIELD].values[0]
                )
            day_ahead_forecast.append({"_time": time_point, FIELD: np.median(points)})

        day_ahead_forecast_df = pd.DataFrame(day_ahead_forecast)
        all_forecasts = pd.concat(
            [all_forecasts, day_ahead_forecast_df], ignore_index=True
        )
        # Merge day_ahead_forecast_df with gci_data on '_time' to align the data
        merged_data = pd.merge(
            day_ahead_forecast_df,
            gci_data,
            on="_time",
            how="inner",
            suffixes=("_forecast", "_actual"),
        )
        # Calculate RMSE
        fc_rmse = np.sqrt(
            mean_squared_error(
                merged_data[FIELD + "_forecast"].values,
                merged_data[FIELD + "_actual"].values,
            )
        )
        rmse_values.append(
            {"rmse": fc_rmse, "_time": day_ahead_forecast_df["_time"].values[0]}
        )

    rmse_values = pd.DataFrame(data=rmse_values)
    all_forecasts = all_forecasts.sort_values(by="_time")

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot historic data
    ax1.plot(
        gci_data["_time"],
        gci_data[FIELD],
        "--",
        color="black",
        label="Historic",
        alpha=0.1,
    )

    # Plot forecast data
    ax1.plot(
        all_forecasts["_time"],
        all_forecasts[FIELD],
        color="green",
        label="Forecast",
    )

    # Set labels and title for primary axis
    ax1.set_xlabel("Date")
    ax1.set_ylabel("GCI [gCO2-eq. / kWh]")
    ax1.set_title(
        f"{FORECAST_DAYS}-day GCI Forecasting with {LOOKBACK_DAYS} days lookback)"
    )
    ax1.legend(loc="upper left")

    # Create secondary y-axis for RMSE
    ax2 = ax1.twinx()
    ax2.plot(rmse_values["_time"], rmse_values["rmse"], "^", color="red", alpha=0.3)
    ax2.set_ylabel("RMSE")

    # Tight layout and display plot
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
