"""Experiment for GCI forecasting"""

from datetime import datetime, timedelta, UTC
from pathlib import Path
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

from src.config.squirrel_conf import Config
from src.data.gci.influxdb import get_gci_trace_data, get_gci_data
from src.forecasting.gci import forecast_gci

FC_VIZ_DIRECTORY = Config.get_local_paths()["viz_path"] / "forecasting"


def demo(forecast_days: int, lookback_days: int):
    """Live demo of forecast."""
    end_point = datetime.now(tz=UTC).replace(microsecond=0, second=0, minute=0)
    start_point = end_point - timedelta(days=lookback_days, hours=1)
    gci_history = get_gci_data(start=start_point, stop=end_point)
    forecast = forecast_gci(gci_history, days=forecast_days, lookback=lookback_days)
    plt.plot(forecast["time"], forecast["gci"])
    plt.xlabel("Time [UTC]")
    plt.xticks(rotation=45)
    plt.ylabel("gCO2-eq/kWh")
    plt.title("GCI Forecast")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "demo.png")


def visualize_simulation(forecast_days: int, lookback_days: int, hourly: bool):
    FC_VIZ_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stop = datetime.fromisoformat("2023-07-08T23:00:00Z")
    start = datetime.fromisoformat("2023-07-01T00:00:00Z")
    gci_hist, forecasts, metrics = _simulate_forecasts(
        gci_data=get_gci_trace_data(start=start, stop=stop),
        forecast_days=forecast_days,
        lookback_days=lookback_days,
        hourly=hourly,
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
    ax1.tick_params(axis="x", labelrotation=45)
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
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "simulation.png")


def parameter_eval(forecast_days: list[int], lookback_range: list[int], hourly: bool):
    """Evaluate forecasting with different parameters."""
    stop = datetime.fromisoformat("2023-12-31T23:00:00Z")
    start = datetime.fromisoformat("2023-01-01T00:00:00Z")
    all_pcc = []
    all_rmse = []
    all_calc = []
    for fc_days in forecast_days:
        pccs = []
        rmses = []
        calcs = []
        for lookback in lookback_range:
            _, _, metrics = _simulate_forecasts(
                gci_data=get_gci_trace_data(start=start, stop=stop),
                forecast_days=fc_days,
                lookback_days=lookback,
                hourly=hourly,
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
    _, ax = plt.subplots()

    # PCC
    ax.imshow(median_pcc, cmap="YlGn")
    ax.set_xticks(np.arange(len(lookback_range)), labels=lookback_range)
    ax.set_xlabel("Lookback days")
    ax.set_yticks(np.arange(len(forecast_days)), labels=forecast_days)
    ax.set_ylabel("Forecasted days")
    for i in range(len(forecast_days)):
        for j in range(len(lookback_range)):
            ax.text(
                j,
                i,
                round(median_pcc[i, j], 3),
                ha="center",
                va="center",
                color="white" if median_pcc[i, j] > 0.8 else "black",
            )
    ax.title.set_text("Median PCC")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "param_eval_pcc.png")
    plt.cla()

    # RMSE
    ax.imshow(median_rmse, cmap="YlGn_r")
    ax.set_xticks(np.arange(len(lookback_range)), labels=lookback_range)
    ax.set_xlabel("Lookback days")
    ax.set_yticks(np.arange(len(forecast_days)), labels=forecast_days)
    ax.set_ylabel("Forecasted days")
    for i in range(len(forecast_days)):
        for j in range(len(lookback_range)):
            ax.text(
                j,
                i,
                round(median_rmse[i, j]),
                ha="center",
                va="center",
                color="white" if median_rmse[i, j] < 85 else "black",
            )
    ax.title.set_text("Median RMSE")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "param_eval_rmse.png")
    plt.cla()

    # Computation Time
    ax.imshow(median_time, cmap="YlGn_r")
    ax.set_xticks(np.arange(len(lookback_range)), labels=lookback_range)
    ax.set_xlabel("Lookback days")
    ax.set_yticks(np.arange(len(forecast_days)), labels=forecast_days)
    ax.set_ylabel("Forecasted days")
    for i in range(len(forecast_days)):
        for j in range(len(lookback_range)):
            ax.text(
                j,
                i,
                round(median_time[i, j], 4),
                ha="center",
                va="center",
                color="white" if median_time[i, j] < 0.04 else "black",
            )
    ax.title.set_text("Median computation time per forecast [s]")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "param_eval_performance.png")
    plt.cla()


def _simulate_forecasts(
    gci_data: pd.DataFrame, forecast_days: int, lookback_days: int, hourly: bool
):
    # Initialize forecasting data
    all_forecasts = pd.DataFrame()
    metrics = []

    # Get timeframe information
    start_point = gci_data["time"].min()
    end_point = gci_data["time"].max()
    days = (end_point - start_point).days

    # Forecasts for the whole time range
    range_end = (days - lookback_days + 1) * 24 if hourly else days - lookback_days + 1
    for i in range(1, range_end):
        # Get window for forecasting
        break_point = (
            pd.to_datetime(end_point - timedelta(hours=i), utc=True, unit="ns")
            if hourly
            else pd.to_datetime(
                end_point - timedelta(days=forecast_days * i), utc=True, unit="ns"
            )
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
        forecast = forecast_gci(data=window, days=forecast_days, lookback=lookback_days)
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
