"""Experiment for GCI forecasting"""

from datetime import datetime, timedelta, UTC
import time

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import root_mean_squared_error, mean_absolute_percentage_error

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data
from src.forecasting.gci import builtin_forecast_gci

FC_VIZ_DIRECTORY = Config.get_local_paths()["viz_path"] / "forecasting"


def demo(forecast_days: int, lookback_days: int):
    """Live demo of forecast."""
    FC_VIZ_DIRECTORY.mkdir(exist_ok=True, parents=True)
    end_point = datetime.now(tz=UTC)
    start_point = end_point - timedelta(days=lookback_days, hours=1)
    gci_history = get_gci_data(start=start_point, stop=end_point)
    forecast = builtin_forecast_gci(
        gci_history, days=forecast_days, lookback=lookback_days
    )
    plt.plot(forecast["time"], forecast["gci"], linewidth=2)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m-%dT%H:%m"))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.xlabel("Time [UTC]")
    plt.xticks(rotation=45)
    plt.ylabel("g$\mathregular{CO_2}$-eq./kWh")
    plt.title("Grid Carbon Intensity Forecast")
    plt.grid(axis="y", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "demo.pdf")


def visualize_simulation(forecast_days: int, lookback_days: int, hourly: bool):
    """Visualize a forecast run."""
    FC_VIZ_DIRECTORY.mkdir(exist_ok=True, parents=True)
    stop = datetime.fromisoformat("2023-07-08T23:00:00Z")
    start = datetime.fromisoformat("2023-07-01T00:00:00Z")
    gci_hist, forecasts, metrics = _simulate_forecasts(
        gci_data=get_gci_data(start=start, stop=stop),
        forecast_days=forecast_days,
        lookback_days=lookback_days,
        hourly=hourly,
    )

    # Plotting
    _, ax1 = plt.subplots(figsize=(10, 6))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))

    # Plot historic data
    ax1.plot(
        gci_hist["time"],
        gci_hist["gci"],
        "--",
        color="black",
        label="Historic",
        alpha=0.2,
        linewidth=2,
    )

    # Plot forecast data
    ax1.plot(
        forecasts["time"],
        forecasts["gci"],
        color="tab:green",
        label="Forecast",
        linewidth=2,
    )

    # Set labels and title for primary axis
    ax1.set_xlabel("Date")
    ax1.tick_params(axis="x", labelrotation=45)
    ax1.set_ylabel("g$\mathregular{CO_2}$-eq./kWh")
    ax1.set_title(
        f"{forecast_days}-day GCI forecasting with {lookback_days} days lookback"
    )
    ax1.legend(loc="upper left")

    # Create secondary y-axis for RMSE
    ax2 = ax1.twinx()
    ax2.step(
        metrics["time"], metrics["rmse"], "^-", color="tab:red", alpha=0.5, where="post"
    )
    ax2.set_ylabel("RMSE")
    ax2.yaxis.label.set_color("tab:red")
    ax2.tick_params(axis="y", colors="tab:red")

    # Create tertiary y-axis for PCC
    ax3 = ax1.twinx()
    ax3.step(
        metrics["time"], metrics["pcc"], "^-", color="tab:blue", alpha=0.5, where="post"
    )
    ax3.set_ylabel("PCC")
    ax3.set_ylim([-1, 1])
    ax3.yaxis.label.set_color("tab:blue")
    ax3.tick_params(axis="y", colors="tab:blue")
    ax3.spines["right"].set_position(("outward", 60))

    # Create 4th y-axis for MAPE
    ax4 = ax1.twinx()
    ax4.step(
        metrics["time"],
        metrics["mape"],
        "^-",
        color="tab:orange",
        alpha=0.5,
        where="post",
    )
    ax4.set_ylabel("MAPE")
    ax4.set_ylim([0, 1])
    ax4.yaxis.label.set_color("tab:orange")
    ax4.tick_params(axis="y", colors="tab:orange")
    ax4.spines["right"].set_position(("outward", 120))

    # Tight layout and display plot
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "simulation.pdf")


def parameter_eval(forecast_days: list[int], lookback_range: list[int], hourly: bool):
    """Evaluate forecasting with different parameters."""
    FC_VIZ_DIRECTORY.mkdir(exist_ok=True, parents=True)
    stop = datetime.fromisoformat("2023-12-31T23:00:00Z")
    start = datetime.fromisoformat("2023-01-01T00:00:00Z")
    all_pcc = []
    all_rmse = []
    all_mape = []
    all_calc = []
    for fc_days in forecast_days:
        pccs = []
        mapes = []
        rmses = []
        calcs = []
        for lookback in lookback_range:
            _, _, metrics = _simulate_forecasts(
                gci_data=get_gci_data(start=start, stop=stop),
                forecast_days=fc_days,
                lookback_days=lookback,
                hourly=hourly,
            )
            pccs.append(np.median(metrics["pcc"]))
            mapes.append(np.median(metrics["mape"]))
            rmses.append(np.median(metrics["rmse"]))
            calcs.append(np.median(metrics["calculation_time"]))
        all_pcc.append(pccs)
        all_rmse.append(rmses)
        all_mape.append(mapes)
        all_calc.append(calcs)

    median_pcc = np.array(all_pcc)
    pcc_thresh = median_pcc.min() + (median_pcc.max() - median_pcc.min()) / 2
    median_rmse = np.array(all_rmse)
    rmse_thresh = median_rmse.min() + (median_rmse.max() - median_rmse.min()) / 2
    median_mape = np.array(all_mape)
    mape_thresh = median_mape.min() + (median_mape.max() - median_mape.min()) / 2
    median_time = np.array(all_calc)
    time_thresh = median_time.min() + (median_time.max() - median_time.min()) / 2
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
                color="white" if median_pcc[i, j] > pcc_thresh else "black",
            )
    ax.title.set_text("Median PCC")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "param_eval_pcc.pdf")
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
                color="white" if median_rmse[i, j] < rmse_thresh else "black",
            )
    ax.title.set_text("Median RMSE")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "param_eval_rmse.pdf")
    plt.cla()

    # MAPE
    ax.imshow(median_mape, cmap="YlGn_r")
    ax.set_xticks(np.arange(len(lookback_range)), labels=lookback_range)
    ax.set_xlabel("Lookback days")
    ax.set_yticks(np.arange(len(forecast_days)), labels=forecast_days)
    ax.set_ylabel("Forecasted days")
    for i in range(len(forecast_days)):
        for j in range(len(lookback_range)):
            ax.text(
                j,
                i,
                round(median_mape[i, j], 3),
                ha="center",
                va="center",
                color="white" if median_mape[i, j] < mape_thresh else "black",
            )
    ax.title.set_text("Median MAPE")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "param_eval_mape.pdf")
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
                color="white" if median_time[i, j] < time_thresh else "black",
            )
    ax.title.set_text("Median computation time per forecast [s]")
    plt.tight_layout()
    plt.savefig(FC_VIZ_DIRECTORY / "param_eval_performance.pdf")
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
    range_start = 24 if hourly else 1
    range_end = (days - lookback_days) * 24 + 1 if hourly else days - lookback_days + 1
    for i in reversed(range(range_start, range_end)):
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
        forecast = builtin_forecast_gci(
            data=window, days=forecast_days, lookback=lookback_days
        )
        toc = time.perf_counter()
        # Evaluate
        rmse, mape, pcc = _evaluate_forecast(forecast=forecast, ground_truth=gci_data)
        metrics.append(
            {
                "rmse": rmse,
                "mape": mape,
                "pcc": pcc,
                "calculation_time": toc - tic,
                "time": forecast["time"].values[0],
            }
        )
        # Append forecast to other forecasts
        all_forecasts = pd.concat([all_forecasts, forecast], ignore_index=False)

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
    rmse = root_mean_squared_error(
        y_pred=merged_data["gci_forecast"].values,
        y_true=merged_data["gci_actual"].values,
    )
    mape = mean_absolute_percentage_error(
        y_pred=merged_data["gci_forecast"].values,
        y_true=merged_data["gci_actual"].values,
    )
    # Calculate Pearson Correlation Coefficient
    pcc = np.corrcoef(merged_data["gci_forecast"], merged_data["gci_actual"])[0][1]
    return rmse, mape, pcc
