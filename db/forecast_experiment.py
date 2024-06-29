"""Experiment for GCI forecasting"""

from datetime import datetime, timedelta, UTC
import sys
import time

from influxdb_client import InfluxDBClient
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

TOKEN = ""
ORG = ""
URL = ""


def _get_gci_data(start: datetime, stop: datetime):
    """Get GCI data from InfluxDB"""
    client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
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
    gci_data = client.query_api().query_data_frame(query=query, org=ORG)
    gci_data = gci_data[["_time", "g_co2eq_per_kWh"]].rename(
        columns={"_time": "time", "g_co2eq_per_kWh": "gci"}
    )
    return gci_data


def _forecast(data: pd.DataFrame, days: int = 1, lookback: int = 2) -> pd.DataFrame:
    latest_ts = data["time"].max()
    forecast_times = pd.date_range(
        start=latest_ts + timedelta(hours=1),
        periods=days * 24,
        freq="h",
        tz="UTC",
    )
    forecast = []
    for time_point in forecast_times:
        points = []
        for day_offset in range(1, lookback + 1):
            past_time_point = time_point - timedelta(days=day_offset)
            if past_time_point < latest_ts:
                points.append(data[data["time"] == past_time_point]["gci"].values[0])
            else:
                for fc_point in forecast:
                    if fc_point["time"] == past_time_point:
                        points.append(fc_point["gci"])
        forecast.append({"time": time_point, "gci": np.median(points)})
    return pd.DataFrame(forecast)


def _simulate_forecasts(gci_data: pd.DataFrame, forecast_days: int, lookback_days: int):
    # Initialize forecasting data
    all_forecasts = pd.DataFrame()
    metrics = []

    # Get timeframe information
    start_point = gci_data["time"].min()
    end_point = gci_data["time"].max()
    days = (end_point - start_point).days

    # Forecasts for the whole time range
    for i in range(1, days - lookback_days + 1):
        # Get window for forecasting
        break_point = pd.to_datetime(
            end_point - timedelta(days=forecast_days * i), utc=True, unit="ns"
        )
        lookback_point = pd.to_datetime(
            break_point - timedelta(days=lookback_days), utc=True, unit="ns"
        )
        if lookback_point < start_point:
            continue
        gci_hist = gci_data[gci_data["time"] < break_point]
        window = gci_hist[gci_hist["time"] >= lookback_point]
        # Execute forecast
        tic = time.perf_counter()
        forecast = _forecast(data=window, days=forecast_days, lookback=lookback_days)
        toc = time.perf_counter()
        # Evaluate
        rmse, pcc = _evaluate_forecast(forecast=forecast, ground_truth=gci_data)
        metrics.append(
            {
                "rmse": rmse,
                "pcc": pcc,
                "calculation_time": toc - tic,
                "time": forecast["time"].values[0],
            }
        )
        # Append forecast to other forecasts
        all_forecasts = pd.concat([all_forecasts, forecast], ignore_index=True)

    all_forecasts = all_forecasts.sort_values(by="time")
    metrics = pd.DataFrame(metrics)

    return gci_data, all_forecasts, metrics


def _evaluate_forecast(forecast: pd.DataFrame, ground_truth: pd.DataFrame):
    """Calculate Root Mean Squared Error (RMSE)
    and Pearson Correlation Coefficient (PCC) of the forecast.

    Both dataframes are expected to have a "time" column with timestamps
    and a "gci" column for the GCI values.
    """

    # Align the data
    merged_data = pd.merge(
        forecast,
        ground_truth,
        on="time",
        how="inner",
        suffixes=("_forecast", "_actual"),
    )
    # Calculate RMSE
    rmse = np.sqrt(
        mean_squared_error(
            merged_data["gci_forecast"].values,
            merged_data["gci_actual"].values,
        )
    )
    # Calculate Pearson Correlation Coefficient
    pcc = np.corrcoef(merged_data["gci_forecast"], merged_data["gci_actual"])[0][1]
    return rmse, pcc


def _visualize_simulation(forecast_days: int = 1, lookback_days: int = 2):
    stop = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    start = stop - timedelta(days=12, hours=1)
    gci_hist, forecasts, metrics = _simulate_forecasts(
        gci_data=_get_gci_data(start=start, stop=stop),
        forecast_days=forecast_days,
        lookback_days=lookback_days,
    )

    # Plotting
    _, ax1 = plt.subplots(figsize=(10, 6))

    # Plot historic data
    ax1.plot(
        gci_hist["time"],
        gci_hist["gci"],
        "--",
        color="black",
        label="Historic",
        alpha=0.1,
    )

    # Plot forecast data
    ax1.plot(
        forecasts["time"],
        forecasts["gci"],
        color="green",
        label="Forecast",
    )

    # Set labels and title for primary axis
    ax1.set_xlabel("Date")
    ax1.set_ylabel("GCI [gCO2-eq. / kWh]")
    ax1.set_title(
        f"{forecast_days}-day GCI Forecasting with {lookback_days} days lookback"
    )
    ax1.legend(loc="upper left")

    # Create secondary y-axis for RMSE
    ax2 = ax1.twinx()
    ax2.step(metrics["time"], metrics["rmse"], "^-", color="red", alpha=0.3)
    ax2.set_ylabel("RMSE")
    ax2.yaxis.label.set_color("red")
    ax2.tick_params(axis="y", colors="red")

    # Create tertiary y-axis for PCC
    ax3 = ax1.twinx()
    ax3.step(metrics["time"], metrics["pcc"], "^-", color="blue", alpha=0.3)
    ax3.set_ylabel("PCC")
    ax3.set_ylim([-1, 1])
    ax3.yaxis.label.set_color("blue")
    ax3.tick_params(axis="y", colors="blue")
    ax3.spines["right"].set_position(("outward", 60))

    # Tight layout and display plot
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def _parameter_opt(forecast_days: list[int], lookback_range: list[int]):
    days = 120
    stop = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    start = stop - timedelta(days=days, hours=1)
    all_pcc = []
    all_rmse = []
    all_calc = []
    for fc_days in forecast_days:
        pccs = []
        rmses = []
        calcs = []
        for lookback in lookback_range:
            _, _, metrics = _simulate_forecasts(
                gci_data=_get_gci_data(start=start, stop=stop),
                forecast_days=fc_days,
                lookback_days=lookback,
            )
            pccs.append(np.median(metrics["pcc"]))
            rmses.append(np.median(metrics["rmse"]))
            calcs.append(np.median(metrics["calculation_time"]))
        all_pcc.append(pccs)
        all_rmse.append(rmses)
        all_calc.append(calcs)

    median_pcc = np.array(all_pcc)
    median_rmse = np.array(all_rmse)
    median_time = np.array(all_calc)
    fig, axs = plt.subplots(ncols=3)

    # PCC
    axs[0].imshow(median_pcc, cmap="YlGn")
    axs[0].set_xticks(np.arange(len(lookback_range)), labels=lookback_range)
    axs[0].set_xlabel("Lookback days")
    axs[0].set_yticks(np.arange(len(forecast_days)), labels=forecast_days)
    axs[0].set_ylabel("Forecasted days")
    for i in range(len(forecast_days)):
        for j in range(len(lookback_range)):
            axs[0].text(
                j,
                i,
                round(median_pcc[i, j], 3),
                ha="center",
                va="center",
                color="white" if median_pcc[i, j] > 0.8 else "black",
            )
    axs[0].title.set_text("Median PCC")

    # RMSE
    axs[1].imshow(median_rmse, cmap="YlGn_r")
    axs[1].set_xticks(np.arange(len(lookback_range)), labels=lookback_range)
    axs[1].set_xlabel("Lookback days")
    axs[1].set_yticks(np.arange(len(forecast_days)), labels=forecast_days)
    axs[1].set_ylabel("Forecasted days")
    for i in range(len(forecast_days)):
        for j in range(len(lookback_range)):
            axs[1].text(
                j,
                i,
                round(median_rmse[i, j]),
                ha="center",
                va="center",
                color="white" if median_rmse[i, j] < 85 else "black",
            )
    axs[1].title.set_text("Median RMSE")

    # Computation Time
    axs[2].imshow(median_time, cmap="YlGn_r")
    axs[2].set_xticks(np.arange(len(lookback_range)), labels=lookback_range)
    axs[2].set_xlabel("Lookback days")
    axs[2].set_yticks(np.arange(len(forecast_days)), labels=forecast_days)
    axs[2].set_ylabel("Forecasted days")
    for i in range(len(forecast_days)):
        for j in range(len(lookback_range)):
            axs[2].text(
                j,
                i,
                round(median_time[i, j], 4),
                ha="center",
                va="center",
                color="white" if median_time[i, j] < 0.04 else "black",
            )
    axs[2].title.set_text("Median computation time per forecast [s]")

    fig.suptitle(f"Squirrel Forecasting Simulation for {days} days")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "opt":
            _parameter_opt(
                forecast_days=[1, 2, 3], lookback_range=[2, 3, 4, 5, 6, 7, 8, 9, 10]
            )
    else:
        _visualize_simulation()
