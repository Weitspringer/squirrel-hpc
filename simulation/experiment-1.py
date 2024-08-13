"""Timeshifting experiment."""

from datetime import datetime, timedelta
from multiprocessing import Queue, Process
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.squirrel_conf import Config
from src.sched.scheduler import Scheduler, TemporalShifting, CarbonAgnosticFifo
from src.sched.timetable import Timetable

# Experiment configuration
ZONES = ["DE", "FR", "GB", "PL", "US-MIDA-PJM"]
START = "2023-01-01T00:00:00+00:00"
DAYS = 364
JOB_CONSUMPTION_WATTS = 150
CLUSTER_PATH = Path("simulation") / "data" / "single-node-cluster.json"
RESULT_DIR = Path("viz") / "simulation" / "exp1"
RESULT_DIR.mkdir(exist_ok=True)


def _sim_schedule(
    submit_date: datetime, influx_options: dict
) -> tuple[float, float, float, float]:
    # Create schedulers
    carbon_agnostic_scheduler = Scheduler(
        strategy=CarbonAgnosticFifo(),
        cluster_info=CLUSTER_PATH,
    )
    timeshift_scheduler = Scheduler(
        strategy=TemporalShifting(),
        cluster_info=CLUSTER_PATH,
    )
    # Construct new time tables
    # Append ground truth data to new timetables (no forecasting error)
    ca_timetable = Timetable()
    ca_timetable.append_historic(
        start=submit_date,
        end=submit_date + timedelta(hours=24),
        options=influx_options,
    )
    ts_timetable = Timetable()
    ts_timetable.append_historic(
        start=submit_date,
        end=submit_date + timedelta(hours=24),
        options=influx_options,
    )
    for i in range(5):
        carbon_agnostic_scheduler.schedule_sbatch(
            timetable=ca_timetable, job_id=str(i), hours=1, partitions=["admin"]
        )
        timeshift_scheduler.schedule_sbatch(
            timetable=ts_timetable, job_id=str(i), hours=1, partitions=["admin"]
        )
    # Calculate carbon-agnostic emissions and average delay
    ca_footprint = 0
    ca_delays = []
    for index, slot in enumerate(ca_timetable.timeslots):
        if len(slot.reserved_resources) == 1:
            ca_delays.append(index)
            ca_footprint += slot.gci * (JOB_CONSUMPTION_WATTS / 1000)
        elif len(slot.reserved_resources) > 1:
            raise RuntimeError(
                "Please use single-node configuration for this experiment!"
            )
    # Calculate timeshifting emissions and average delay
    ts_footprint = 0
    ts_delays = []
    for index, slot in enumerate(ts_timetable.timeslots):
        if len(slot.reserved_resources) == 1:
            ts_delays.append(index)
            ts_footprint += slot.gci * (JOB_CONSUMPTION_WATTS / 1000)
        elif len(slot.reserved_resources) > 1:
            raise RuntimeError(
                "Please use single-node configuration for this experiment!"
            )
    return ca_footprint, np.average(ca_delays), ts_footprint, np.average(ts_delays)


def _simulate(zone: str, queue: Queue) -> tuple[list, list, list, list, list]:
    # Create date range for job submissions
    first_submit_date = datetime.fromisoformat(START)
    submit_dates = pd.date_range(
        start=first_submit_date,
        periods=DAYS * 24,
        freq="h",
        tz="UTC",
    )
    ca_footprints = []
    ca_delays = []
    ts_footprints = []
    ts_delays = []
    influx_options = Config.get_influx_config()["gci"]["history"]
    influx_options.get("tags").update({"zone": zone})
    for submit_date in submit_dates:
        ca_footprint, ca_delay, ts_footprint, ts_delay = _sim_schedule(
            submit_date=submit_date, influx_options=influx_options
        )
        ca_footprints.append(round(ca_footprint, 2))
        ca_delays.append(ca_delay)
        ts_footprints.append(round(ts_footprint, 2))
        ts_delays.append(ts_delay)
    queue.put(
        (
            zone,
            {
                "ca_fp": ca_footprints,
                "ca_d": ca_delays,
                "ts_fp": ts_footprints,
                "ts_d": ts_delays,
            },
        )
    )


# Scheduling for multiple timetables
zoned_ca_footprints = {}
zoned_ca_delays = {}
zoned_ts_footprints = {}
zoned_ts_delays = {}
q = Queue()
for z in ZONES:
    p = Process(target=_simulate, args=(z, q))
    p.start()
for _ in range(len(ZONES)):
    z, results = q.get()
    zoned_ca_footprints.update({z: results.get("ca_fp")})
    zoned_ca_delays.update({z: results.get("ca_d")})
    zoned_ts_footprints.update({z: results.get("ts_fp")})
    zoned_ts_delays.update({z: results.get("ts_d")})
zoned_ca_footprints = dict(sorted(zoned_ca_footprints.items()))
zoned_ca_delays = dict(sorted(zoned_ca_delays.items()))
zoned_ts_footprints = dict(sorted(zoned_ts_footprints.items()))
zoned_ts_delays = dict(sorted(zoned_ts_delays.items()))

##### Plotting
hours = range(24)

# Plot savings per hour of day
zoned_ts_savings_hourly_median = {}
for zone, ts_footprints in zoned_ts_footprints.items():
    ts_savings_hourly_median = np.ma.median(
        np.subtract(1, np.divide(ts_footprints, zoned_ca_footprints.get(zone))).reshape(
            (DAYS, 24)
        ),
        axis=0,
    )
    plt.plot(hours, ts_savings_hourly_median, label=zone)
plt.ylabel("Median Fraction of Emissions Saved")
# plt.title("E1: Median Fractional Carbon Savings of Timeshifting (vs. FIFO)")
plt.xlabel("Hour of Day")
plt.legend(loc="upper left", ncols=len(ZONES))
plt.ylim(0, 1)
plt.tight_layout()
plt.savefig(RESULT_DIR / "exp1-result.png")
plt.clf()

## Plot average job delay
for zone, ts_delays in zoned_ts_delays.items():
    ts_hourly_delay = np.ma.median(np.reshape(ts_delays, (DAYS, 24)), axis=0)
    # ca_hourly_delay = np.ma.median(np.reshape(ca_delays, (DAYS, 24)), axis=0)
    # plt.plot(hours, ca_hourly_delay, color="blue", label="FIFO")
    plt.plot(hours, ts_hourly_delay, label=zone)
plt.ylabel("Avg. Delay [hours]")
plt.xlabel("Hour of Day")
plt.legend()
plt.tight_layout()
plt.savefig(RESULT_DIR / "exp1-delay.png")
