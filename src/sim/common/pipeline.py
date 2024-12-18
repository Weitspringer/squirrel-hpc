"""Pipeline for comparison of two scheduling strategies."""

from datetime import datetime, timedelta
from multiprocessing import Queue, Process
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np
import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data
from src.sched.scheduler import Scheduler, PlanningStrategy
from src.sched.timetable import Timetable

# pylint: disable=too-many-arguments, too-many-locals, too-few-public-methods


class JobSubmission:
    """Job submission for simulation"""

    def __init__(
        self,
        job_id: str,
        partitions: list[str],
        reserved_hours: int,
        num_gpus: int,
        gpu_name: str,
        power_draws: dict[str, list[int]],
    ):
        self.id = job_id
        self.partitions = partitions
        self.reserved_hours = reserved_hours
        self.num_gpus = num_gpus
        self.gpu_name = gpu_name
        self.power_draws = power_draws
        self.power_draw_rc = 0  # Read counter for power draws


def adjust_plot_font():
    """Adjust plot font sizes"""
    small_size = 10
    medium_size = 12
    bigger_size = 14
    plt.rc("font", size=small_size)  # controls default text sizes
    plt.rc("axes", titlesize=medium_size)  # fontsize of the axes title
    plt.rc("axes", labelsize=medium_size)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=medium_size)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=medium_size)  # fontsize of the tick labels
    plt.rc("legend", fontsize=medium_size)  # legend fontsize
    plt.rc("figure", titlesize=bigger_size)  # fontsize of the figure title


def _sim_schedule(
    strategy: PlanningStrategy,
    gci_data: pd.DataFrame,
    forecasted_gci: pd.DataFrame,
    jobs: list[JobSubmission],
    cluster_path: Path,
    cluster_pue: float,
) -> tuple[float, float]:
    """Schedule a job set, all with the same submit date.
    Returns scheduling footprint and mean job delay.
    """
    # Create scheduler
    scheduler = Scheduler(
        strategy=strategy,
        cluster_info=cluster_path,
    )
    # Construct new time tables
    timetable = Timetable()
    timetable.append_direct(gci_data)
    for job in jobs:
        scheduler.schedule_sbatch(
            timetable=timetable,
            job_id=job.id,
            hours=job.reserved_hours,
            partitions=job.partitions,
            num_gpus=job.num_gpus,
            gpu_name=job.gpu_name,
        )
    footprint = 0
    delays = []
    for index, slot in enumerate(timetable.timeslots):
        for job in jobs:
            reservation = slot.get_reservation(job.id)
            if reservation:
                watts = job.power_draws.get(reservation.get("node"))[job.power_draw_rc]
                job.power_draw_rc += 1
                delays.append(index)
                footprint += slot.gci * (
                    (watts / 1000)
                    * cluster_pue
                    * (
                        (
                            datetime.fromisoformat(reservation.get("end"))
                            - datetime.fromisoformat(reservation.get("start"))
                        ).seconds
                        / 60
                        / 60
                    )
                )
    for job in jobs:
        job.power_draw_rc = 0
    return footprint, np.mean(delays)


def _sim_schedule_forecasted(
    strategy: PlanningStrategy,
    gci_data: pd.DataFrame,
    forecasted_gci: pd.DataFrame,
    jobs: list[JobSubmission],
    cluster_path: Path,
    cluster_pue: float,
) -> tuple[float, float]:
    """Schedule a job set, all with the same submit date.
    The GCI is not set from history, but forecasted.
    Returns scheduling footprint and mean job delay.
    """
    # Create scheduler
    scheduler = Scheduler(
        strategy=strategy,
        cluster_info=cluster_path,
    )
    # Construct new time tables
    timetable = Timetable()
    timetable.append_direct(forecasted_gci)
    for job in jobs:
        scheduler.schedule_sbatch(
            timetable=timetable,
            job_id=job.id,
            hours=job.reserved_hours,
            partitions=job.partitions,
            num_gpus=job.num_gpus,
            gpu_name=job.gpu_name,
        )
    footprint = 0
    delays = []
    for index, slot in enumerate(timetable.timeslots):
        for job in jobs:
            reservation = slot.get_reservation(job.id)
            if reservation:
                watts = job.power_draws.get(reservation.get("node"))[job.power_draw_rc]
                job.power_draw_rc += 1
                delays.append(index)
                real_gci = gci_data.loc[
                    gci_data["time"] == pd.Timestamp(slot.start)
                ].iloc[0]["gci"]
                footprint += real_gci * (
                    (watts / 1000)
                    * cluster_pue
                    * (
                        (
                            datetime.fromisoformat(reservation.get("end"))
                            - datetime.fromisoformat(reservation.get("start"))
                        ).seconds
                        / 60
                        / 60
                    )
                )
    for job in jobs:
        job.power_draw_rc = 0
    return footprint, np.mean(delays)


def _compare(
    pue: float,
    zone: str,
    start: str,
    days: int,
    lookahead_hours: int,
    jobs_1: dict[str, dict[str, int]],
    jobs_2: dict[str, dict[str, int]],
    cluster_path: Path,
    strat_1: PlanningStrategy,
    strat_2: PlanningStrategy,
    forecasted: bool,
    queue: Queue,
) -> None:
    # Create date range for job submissions
    first_submit_date = datetime.fromisoformat(start)
    submit_dates = pd.date_range(
        start=first_submit_date,
        periods=days * lookahead_hours,
        freq="h",
        tz="UTC",
    )
    footprints_1 = []
    delays_1 = []
    footprints_2 = []
    delays_2 = []
    # Get the GCI data
    if not forecasted:
        _sim_method = _sim_schedule
        forecasted_gci = None
    else:
        _sim_method = _sim_schedule_forecasted
        influx_options = Config.get_influx_config()["gci"]["forecast"]
        influx_options.get("tags").update({"zone": zone})
        forecasted_gci = get_gci_data(
            submit_dates[0],
            submit_dates[-1] + timedelta(hours=lookahead_hours + 1),
            options=influx_options,
        )
    influx_options = Config.get_influx_config()["gci"]["history"]
    influx_options.get("tags").update({"zone": zone})
    gci_data = get_gci_data(
        submit_dates[0],
        submit_dates[-1] + timedelta(hours=lookahead_hours + 1),
        options=influx_options,
    )
    # Simulate for submit dates
    for submit_date in submit_dates:
        part_gci = gci_data[
            (gci_data["time"] >= submit_date + timedelta(hours=1))
            & (gci_data["time"] <= submit_date + timedelta(hours=lookahead_hours))
        ]
        if forecasted_gci is not None:
            part_forecasted = forecasted_gci[
                (gci_data["time"] >= submit_date + timedelta(hours=1))
                & (gci_data["time"] <= submit_date + timedelta(hours=lookahead_hours))
            ]
        else:
            part_forecasted = None
        footprint_1, delay_1 = _sim_method(
            strategy=strat_1,
            gci_data=part_gci,
            forecasted_gci=part_forecasted,
            jobs=jobs_1,
            cluster_path=cluster_path,
            cluster_pue=pue,
        )
        footprint_2, delay_2 = _sim_method(
            strategy=strat_2,
            gci_data=part_gci,
            forecasted_gci=part_forecasted,
            jobs=jobs_2,
            cluster_path=cluster_path,
            cluster_pue=pue,
        )
        footprints_1.append(round(footprint_1, 2))
        delays_1.append(delay_1)
        footprints_2.append(round(footprint_2, 2))
        delays_2.append(delay_2)
    queue.put(
        (
            zone,
            {
                "fp_1": footprints_1,
                "d_1": delays_1,
                "fp_2": footprints_2,
                "d_2": delays_2,
            },
            submit_dates,
        )
    )


def main(
    pue: float,
    zones: list[dict],
    start: str,
    days: int,
    lookahead_hours: int,
    jobs_1: dict[str, dict[str, int]],
    jobs_2: dict[str, dict[str, int]],
    cluster_path: Path,
    result_dir: Path,
    strat_1: PlanningStrategy,
    strat_2: PlanningStrategy,
    forecasting: bool,
) -> None:
    """Run a scenario."""
    data_dir = result_dir / "data"
    data_dir.mkdir(exist_ok=True, parents=True)
    # Scheduling for multiple timetables
    result = []
    q = Queue()
    for z in zones:
        p = Process(
            target=_compare,
            args=(
                pue,
                z.get("name"),
                start,
                days,
                lookahead_hours,
                jobs_1,
                jobs_2,
                cluster_path,
                strat_1,
                strat_2,
                forecasting,
                q,
            ),
        )
        p.start()
    for _ in range(len(zones)):
        z, results, submit_dates = q.get()
        for index, submit_date in enumerate(submit_dates):
            row_entry = {
                "zone": z,
                "submit_date": submit_date,
                "footprint_baseline": results.get("fp_1")[index],
                "delay_baseline": results.get("d_1")[index],
                "footprint_benchmark": results.get("fp_2")[index],
                "delay_benchmark": results.get("d_2")[index],
            }
            result.append(row_entry)
    result_df = pd.DataFrame(result)
    result_df.sort_values(by=["zone", "submit_date"], inplace=True)
    result_df.to_csv(data_dir / "results.csv", index=False)


def plot(
    days: int,
    result_dir: Path,
    zones_dict: list[dict],
) -> None:
    """Visualize scenario results."""
    # pylint: disable=anomalous-backslash-in-string

    adjust_plot_font()

    ### Load result data
    data_dir = result_dir / "data"
    result_df = pd.read_csv(data_dir / "results.csv")
    zones = sorted(result_df["zone"].unique())

    ### Dynamically set unique colors for zones
    if len(zones) <= 8:
        cm = plt.get_cmap("Set2")
    elif len(zones) <= 10:
        cm = plt.get_cmap("tab10")
    elif len(zones) <= 20:
        cm = plt.get_cmap("tab20")
    else:
        cm = plt.get_cmap("hsv")
    cmaplist = [cm(1.0 * i / len(zones)) for i in range(len(zones))]
    zone_colors = {}
    for idx, color in enumerate(cmaplist):
        zone_colors.update({zones[idx]: color})

    ### Calculate statistics
    stats = []
    res_relative = {}
    res_absolute = {}
    res_avg_rel = {}
    res_delay = {}
    res_hours = {}
    utc_shifts = {z.get("name"): z.get("utc_shift_hours") for z in zones_dict}
    for zone in zones:
        # Calculate emissions
        footprints_baseline = result_df[result_df["zone"] == zone][
            "footprint_baseline"
        ].to_list()
        footprints_benchmark = result_df[result_df["zone"] == zone][
            "footprint_benchmark"
        ].to_list()
        # Relative and absolute savings
        relative_savings = np.subtract(
            1, np.divide(footprints_benchmark, footprints_baseline)
        )
        absolute_savings = np.subtract(footprints_baseline, footprints_benchmark)
        # Delay
        benchmark_delays = footprints_baseline = result_df[result_df["zone"] == zone][
            "delay_benchmark"
        ].to_list()
        benchmark_delays_hourly = list(
            np.ma.mean(np.reshape(benchmark_delays, (days, 24)), axis=0)
        )
        # Stats
        min_sav_rel = round(np.min(relative_savings), 4)
        max_sav_rel = round(np.max(relative_savings), 4)
        avg_sav_rel = round(np.mean(relative_savings), 4)
        min_sav_abs = round(np.min(absolute_savings), 4)
        max_sav_abs = round(np.max(absolute_savings), 4)
        avg_sav_abs = round(np.mean(absolute_savings), 4)
        avg_del = round(np.mean(benchmark_delays_hourly), 4)
        utc_shift = utc_shifts.get(zone)
        stats.append(
            {
                "zone": zone,
                "utc_shift_hours": utc_shift,
                "min_savings_rel": min_sav_rel,
                "max_savings_rel": max_sav_rel,
                "avg_savings_rel": avg_sav_rel,
                "min_savings_gCO2eq": min_sav_abs,
                "max_savings_gCO2eq": max_sav_abs,
                "avg_savings_gCO2eq": avg_sav_abs,
                "avg_delay_hours": avg_del,
            }
        )
        savings_hourly_avg = list(
            np.ma.mean(
                relative_savings.reshape((days, 24)),
                axis=0,
            )
        )
        savings_hourly_absolute_avg = list(
            np.ma.mean(absolute_savings.reshape((days, 24)), axis=0)
        )
        # Normalize to local time
        hours = []
        for hour in range(24):
            hour += utc_shift
            hour = hour % 24
            hours.append(hour)
        min_index = hours.index(min(hours))
        if min_index != 0:
            lower = hours[min_index:]
            upper = hours[:min_index]
            hours = lower + upper
            lower = savings_hourly_avg[min_index:]
            upper = savings_hourly_avg[:min_index]
            savings_hourly_avg = lower + upper
            lower = savings_hourly_absolute_avg[min_index:]
            upper = savings_hourly_absolute_avg[:min_index]
            savings_hourly_absolute_avg = lower + upper
            lower = benchmark_delays_hourly[min_index:]
            upper = benchmark_delays_hourly[:min_index]
            benchmark_delays_hourly = lower + upper
        # Data for plotting
        res_hours.update({zone: hours})
        res_relative.update({zone: savings_hourly_avg})
        res_absolute.update({zone: savings_hourly_absolute_avg})
        res_delay.update({zone: benchmark_delays_hourly})
        res_avg_rel.update({zone: (np.mean(savings_hourly_avg), zone_colors.get(zone))})

    ### MEAN RELATIVE SAVINGS
    res_avg_rel_sorted = dict(
        sorted(res_avg_rel.items(), key=lambda item: item[1][0], reverse=True)
    )
    res_ar_values = list(map(lambda x: x[0] * 100, res_avg_rel_sorted.values()))
    min_v = min(res_ar_values)
    max_v = max(res_ar_values)
    res_ar_colors = list(map(lambda x: x[1], res_avg_rel_sorted.values()))
    plt.bar(
        range(len(res_ar_values)),
        res_ar_values,
        align="center",
        color=res_ar_colors,
    )
    plt.gca().axes.set_axisbelow(True)
    plt.xticks(range(len(res_ar_values)), list(res_avg_rel_sorted.keys()))
    h_lim = 0
    if min_v < 0:
        plt.axhspan(0, min_v, color="tab:red", alpha=0.1, zorder=-100)
        h_lim = min_v - 2
    if max_v < 35:
        max_v = 35
    plt.ylim(h_lim, max_v)
    plt.ylabel("g$\mathregular{CO_2}$e Savings")
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(base=5))
    plt.grid(axis="y", linewidth=1, alpha=0.5)
    plt.tight_layout()
    plt.savefig(result_dir / "avg-savings-relative.pdf")
    plt.clf()

    ### DELAY
    for zone in zones:
        plt.plot(
            res_hours.get(zone),
            res_delay.get(zone),
            label=zone,
            color=zone_colors.get(zone),
            linewidth=2,
            alpha=0.7,
        )
    plt.locator_params(axis="x", nbins=12)
    plt.gca().axes.set_axisbelow(True)
    plt.ylabel("Mean Job Delay")
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(base=2))
    plt.ylim(0, 24)
    plt.xlabel("Workload Submission Time")
    plt.xlim(0, 23.9)
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%dh"))
    plt.grid(axis="y", linewidth=1, alpha=0.2)
    plt.grid(axis="x", linewidth=1, alpha=0.2)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=len(zones))
    plt.tight_layout()
    plt.savefig(result_dir / "delay.pdf")
    plt.clf()

    ### ABSOLUTE SAVINGS
    min_v = 0
    max_v = 0
    for zone, res_abs in res_absolute.items():
        max_val = max(res_abs)
        min_val = min(res_abs)
        min_v = min(min_val, min_v)
        max_v = max(max_val, max_v)
        plt.plot(
            res_hours.get(zone),
            res_abs,
            label=zone,
            color=zone_colors.get(zone),
            linewidth=2,
        )
    plt.locator_params(axis="x", nbins=12)
    plt.gca().axes.set_axisbelow(True)
    plt.ylabel("Mean $\mathregular{CO_2}$e Saved")
    plt.xlabel("Workload Submission Time")
    plt.xlim(0, 23.9)
    if min_v < 0:
        h_lim = min_v - 10
        plt.axhspan(0, h_lim, color="tab:red", alpha=0.1, zorder=-100)
    max_v += 10
    plt.ylim(h_lim, max_v)
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%dg"))
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(base=50))
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=len(zones))
    # plt.yscale("symlog", base=10)
    plt.grid(axis="y", linewidth=1, alpha=0.3)
    plt.grid(axis="x", linewidth=1, alpha=0.3)
    plt.tight_layout()
    plt.savefig(result_dir / "savings-absolute.pdf")
    plt.clf()

    ### RELATIVE SAVINGS
    min_v = 0
    max_v = 0
    for zone, res_rel in res_relative.items():
        res_rel = list(map(lambda x: x * 100, res_rel))
        min_val = min(res_rel)
        max_val = max(res_rel)
        min_v = min(min_val, min_v)
        max_v = max(max_val, max_v)
        plt.plot(
            res_hours.get(zone),
            res_rel,
            label=zone,
            color=zone_colors.get(zone),
            linewidth=2,
        )
    plt.locator_params(axis="x", nbins=12)
    plt.gca().axes.set_axisbelow(True)
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(base=10))
    plt.ylabel("Mean g$\mathregular{CO_2}$e Saved")
    if min_v < 0:
        h_lim = min_v - 1
        plt.axhspan(0, h_lim, color="tab:red", alpha=0.1, zorder=-100)
    if max_v < 45:
        max_v = 45
    else:
        max_v += 2
    plt.ylim(h_lim, max_v)
    plt.xlabel("Workload Submission Time")
    plt.xlim(0, 23.99)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=len(zones))
    plt.grid(axis="y", linewidth=1, alpha=0.3)
    plt.grid(axis="x", linewidth=1, alpha=0.3)
    plt.tight_layout()
    plt.savefig(result_dir / "savings-relative.pdf")
    plt.clf()

    ### Save stats
    stats_df = pd.DataFrame(stats)
    stats_df = stats_df.set_index(keys=["zone"])
    stats_df.to_csv(data_dir / "stats.csv")


def plot_year_gci(year: str, zones_dict: list[dict], save_path: Path):
    """Plot median GCI in the given year for each hour of the day."""
    # pylint: disable=anomalous-backslash-in-string

    adjust_plot_font()
    ### Dynamically set unique colors for zones
    save_path.parent.mkdir(parents=True, exist_ok=True)
    zones = sorted([x.get("name") for x in zones_dict])
    if len(zones) <= 8:
        cm = plt.get_cmap("Set2")
    elif len(zones) <= 10:
        cm = plt.get_cmap("tab10")
    elif len(zones) <= 20:
        cm = plt.get_cmap("tab20")
    else:
        cm = plt.get_cmap("hsv")
    cmaplist = [cm(1.0 * i / len(zones)) for i in range(len(zones))]
    zone_colors = {}
    for idx, color in enumerate(cmaplist):
        zone_colors.update({zones[idx]: color})
    # Get UTC time shifts for localization
    utc_shifts = {z.get("name"): z.get("utc_shift_hours") for z in zones_dict}
    # Get data for each zone
    influx_options = Config.get_influx_config()["gci"]["history"]
    for zone in zones:
        influx_options.get("tags").update({"zone": zone})
        gci_data = get_gci_data(
            pd.to_datetime(f"{int(year)-1}-12-31T23:00:00+00:00"),
            pd.to_datetime(f"{int(year)}-12-31T23:01:00+00:00"),
            options=influx_options,
        )
        gci_hourly = list(
            np.ma.mean(np.reshape(gci_data["gci"].to_list(), (365, 24)), axis=0)
        )
        # Localize time
        utc_shift = utc_shifts.get(zone)
        hours = []
        for hour in range(24):
            hour += utc_shift
            hour = hour % 24
            hours.append(hour)
        min_index = hours.index(min(hours))
        gci_hourly = list(gci_hourly)
        if min_index != 0:
            lower = hours[min_index:]
            upper = hours[:min_index]
            hours = lower + upper
            lower = gci_hourly[min_index:]
            upper = gci_hourly[:min_index]
            gci_hourly = lower + upper
        plt.plot(
            hours, gci_hourly, color=zone_colors.get(zone), label=zone, linewidth=2
        )
    plt.locator_params(axis="x", nbins=12)
    plt.gca().axes.set_axisbelow(True)
    plt.xlabel("Day Hour")
    plt.xlim(0, 23.99)
    plt.ylabel("Mean g$\mathregular{CO_2}$e/kWh")
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%dg"))
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=len(zones))
    plt.grid(axis="y", linewidth=1, alpha=0.3)
    plt.grid(axis="x", linewidth=1, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.clf()
