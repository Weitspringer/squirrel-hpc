"""Pipeline for comparison of two scheduling strategies."""

from datetime import datetime, timedelta
from multiprocessing import Queue, Process
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data
from src.sched.scheduler import Scheduler, PlanningStrategy
from src.sched.timetable import Timetable


def _sim_schedule(
    strategy: PlanningStrategy,
    submit_date: datetime,
    influx_options: dict,
    jobs: dict[str, dict[str, int]],
    cluster_path: Path,
    hours: int = 24,
) -> tuple[float, float]:
    """Schedule a job set, all with the same submit date.
    Returns scheduling footprint and average job delay.
    """
    # Create scheduler
    scheduler = Scheduler(
        strategy=strategy,
        cluster_info=cluster_path,
    )
    # Construct new time tables
    # Append ground truth data to new timetables (no forecasting error)
    timetable = Timetable()
    timetable.append_historic(
        start=submit_date,
        end=submit_date + timedelta(hours=hours),
        options=influx_options,
    )
    for job_id in jobs.keys():
        scheduler.schedule_sbatch(
            timetable=timetable, job_id=job_id, hours=1, partitions=["admin"]
        )
    footprint = 0
    delays = []
    for index, slot in enumerate(timetable.timeslots):
        for key, consumptions in jobs.items():
            reservation = slot.get_reservation(key)
            if reservation:
                watts = consumptions.get(reservation.get("node"))
                delays.append(index)
                footprint += slot.gci * (
                    (watts / 1000)
                    * (
                        (
                            datetime.fromisoformat(reservation.get("end"))
                            - datetime.fromisoformat(reservation.get("start"))
                        ).seconds
                        / 60
                        / 60
                    )
                )
    return footprint, np.average(delays)


def _sim_schedule_forecasted(
    strategy: PlanningStrategy,
    start_date: str,
    submit_date: datetime,
    influx_options: dict,
    jobs: dict[str, dict[str, int]],
    cluster_path: Path,
    hours: int = 24,
) -> tuple[float, float]:
    """Schedule a job set, all with the same submit date.
    The GCI is not set from history, but forecasted.
    Returns scheduling footprint and average job delay.
    """
    # Get ground truth GCI data
    gci_hist = get_gci_data(
        start=datetime.fromisoformat(start_date),
        stop=datetime.fromisoformat(start_date) + timedelta(days=hours + 1),
        options=influx_options,
    )
    # Create scheduler
    scheduler = Scheduler(
        strategy=strategy,
        cluster_info=cluster_path,
    )
    # Construct new time tables
    timetable = Timetable()
    timetable.append_forecast(
        start=submit_date,
        forecast_days=1,
        lookback_days=2,
        options=influx_options,
    )
    for job_id in jobs.keys():
        scheduler.schedule_sbatch(
            timetable=timetable, job_id=job_id, hours=1, partitions=["admin"]
        )
    footprint = 0
    delays = []
    for index, slot in enumerate(timetable.timeslots):
        for key, consumptions in jobs.items():
            reservation = slot.get_reservation(key)
            if reservation:
                watts = consumptions.get(reservation.get("node"))
                delays.append(index)
                real_gci = gci_hist.loc[
                    gci_hist["time"] == pd.Timestamp(slot.start)
                ].iloc[0]["gci"]
                footprint += real_gci * (
                    (watts / 1000)
                    * (
                        (
                            datetime.fromisoformat(reservation.get("end"))
                            - datetime.fromisoformat(reservation.get("start"))
                        ).seconds
                        / 60
                        / 60
                    )
                )
    return footprint, np.average(delays)


def _compare(
    zone: str,
    start: str,
    days: int,
    lookahead_hours: int,
    jobs: dict[str, dict[str, int]],
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
    influx_options = Config.get_influx_config()["gci"]["history"]
    influx_options.get("tags").update({"zone": zone})
    for submit_date in submit_dates:
        sim_method = _sim_schedule
        if not forecasted:
            sim_method = _sim_schedule
        else:
            sim_method = _sim_schedule_forecasted
        footprint_1, delay_1 = sim_method(
            strategy=strat_1,
            submit_date=submit_date,
            influx_options=influx_options,
            jobs=jobs,
            cluster_path=cluster_path,
            hours=lookahead_hours,
        )
        footprint_2, delay_2 = sim_method(
            strategy=strat_2,
            submit_date=submit_date,
            influx_options=influx_options,
            jobs=jobs,
            cluster_path=cluster_path,
            hours=lookahead_hours,
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
        )
    )


def main(
    zones: list[str],
    start: str,
    days: int,
    lookahead_hours: int,
    jobs: dict[str, dict[str, int]],
    cluster_path: Path,
    result_dir: Path,
    strat_1: PlanningStrategy,
    strat_2: PlanningStrategy,
    forecasting: bool,
) -> None:
    result_dir.mkdir(exist_ok=True, parents=True)
    # Scheduling for multiple timetables
    zoned_1_footprints = {}
    zoned_1_delays = {}
    zoned_2_footprints = {}
    zoned_2_delays = {}
    q = Queue()
    for z in zones:
        p = Process(
            target=_compare,
            args=(
                z,
                start,
                days,
                lookahead_hours,
                jobs,
                cluster_path,
                strat_1,
                strat_2,
                forecasting,
                q,
            ),
        )
        p.start()
    for _ in range(len(zones)):
        z, results = q.get()
        zoned_1_footprints.update({z: results.get("fp_1")})
        zoned_1_delays.update({z: results.get("d_1")})
        zoned_2_footprints.update({z: results.get("fp_2")})
        zoned_2_delays.update({z: results.get("d_2")})
    zoned_1_footprints = dict(sorted(zoned_1_footprints.items()))
    zoned_1_delays = dict(sorted(zoned_1_delays.items()))
    zoned_2_footprints = dict(sorted(zoned_2_footprints.items()))
    zoned_2_delays = dict(sorted(zoned_2_delays.items()))

    ##### Plotting
    hours = range(24)

    ## Set unique colors for zones
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

    stats = []
    res_relative = {}
    res_absolute = {}
    res_avg_rel = {}
    ## Plot savings
    for zone, footprints_2 in zoned_2_footprints.items():
        relative_savings = np.subtract(
            1, np.divide(footprints_2, zoned_1_footprints.get(zone))
        )
        absolute_savings = np.subtract(zoned_1_footprints.get(zone), footprints_2)
        min_sav_rel = round(np.min(relative_savings), 2)
        max_sav_rel = round(np.max(relative_savings), 2)
        min_sav_abs = round(np.min(absolute_savings), 2)
        max_sav_abs = round(np.max(absolute_savings), 2)
        stats.append(
            {
                "zone": zone,
                "min_savings_rel": min_sav_rel,
                "max_savings_rel": max_sav_rel,
                "min_savings_gCO2eq": min_sav_abs,
                "max_savings_gCO2eq": max_sav_abs,
            }
        )
        savings_hourly_median = np.ma.median(
            relative_savings.reshape((days, 24)),
            axis=0,
        )
        savings_hourly_absolute_median = np.ma.median(
            absolute_savings.reshape((days, 24)), axis=0
        )

        res_relative.update({zone: savings_hourly_median})
        res_absolute.update({zone: savings_hourly_absolute_median})
        res_avg_rel.update(
            {zone: (np.average(savings_hourly_median), zone_colors.get(zone))}
        )

    ### Plot relative savings per hour of day
    for zone, res_rel in res_relative.items():
        plt.plot(hours, res_rel, label=zone, color=zone_colors.get(zone))
    plt.ylabel("Median Fraction of Emissions Saved")
    plt.xlabel("Hour of Day")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.ylim(-0.2, 1)
    plt.grid(axis="y", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(result_dir / "med-relative.pdf")
    plt.clf()

    ### Plot average relative savings per hour of day (by zone)
    res_avg_rel_sorted = dict(
        sorted(res_avg_rel.items(), key=lambda item: item[1][0], reverse=True)
    )
    res_ar_values = list(map(lambda x: x[0], res_avg_rel_sorted.values()))
    res_ar_colors = list(map(lambda x: x[1], res_avg_rel_sorted.values()))
    plt.bar(
        range(len(res_ar_values)),
        res_ar_values,
        align="center",
        color=res_ar_colors,
    )
    plt.xticks(range(len(res_ar_values)), list(res_avg_rel_sorted.keys()))
    plt.ylim(0, 1)
    plt.ylabel("Average of Median Relative Savings")
    plt.grid(axis="y", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(result_dir / "avg-med-relative.pdf")
    plt.clf()

    ### Plot absolute savings per hour of day
    for zone, res_abs in res_absolute.items():
        plt.plot(hours, res_abs, label=zone, color=zone_colors.get(zone))
    plt.ylabel("Median Emissions Saved [gCO2eq]")
    plt.xlabel("Hour of Day")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.yscale("log", base=10)
    plt.grid(axis="y", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(result_dir / "med-absolute.pdf")
    plt.clf()

    ## Plot average job delay
    for zone, ts_delays in zoned_2_delays.items():
        ts_hourly_delay = np.ma.median(np.reshape(ts_delays, (days, 24)), axis=0)
        # ca_hourly_delay = np.ma.median(np.reshape(ca_delays, (DAYS, 24)), axis=0)
        # plt.plot(hours, ca_hourly_delay, color="blue", label="FIFO")
        plt.plot(hours, ts_hourly_delay, label=zone, color=zone_colors.get(zone))
    plt.ylabel("Avg. Delay [hours]")
    plt.xlabel("Hour of Day")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout()
    plt.savefig(result_dir / "delay.pdf")

    stats_df = pd.DataFrame(stats)
    stats_df = stats_df.set_index(keys=["zone"])
    stats_df.to_csv(result_dir / "stats.csv")
