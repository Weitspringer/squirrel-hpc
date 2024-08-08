"""Timeshifting experiment."""

from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.sched.scheduler import Scheduler, TemporalShifting, CarbonAgnosticFifo
from src.sched.timetable import Timetable

# Experiment configuration
START = "2023-01-01T00:00:00+00:00"
DAYS = 364
SAMPLE_DAY_START = 100
SAMPLE_DAY_END = 105
JOB_CONSUMPTION_WATTS = 150
CLUSTER_PATH = Path("simulation") / "data" / "single-node-cluster.json"
RESULT_DIR = Path("viz") / "simulation" / "exp1"
RESULT_DIR.mkdir(exist_ok=True)

# Create schedulers
carbon_agnostic_scheduler = Scheduler(
    strategy=CarbonAgnosticFifo(),
    cluster_info=CLUSTER_PATH,
)
timeshift_scheduler = Scheduler(
    strategy=TemporalShifting(),
    cluster_info=CLUSTER_PATH,
)
# Create date range for job submissions
first_submit_date = datetime.fromisoformat(START)
submit_dates = pd.date_range(
    start=first_submit_date,
    periods=DAYS * 24,
    freq="h",
    tz="UTC",
)
# Scheduling for multiple timetables
ca_footprints = []
ca_delays = []
ts_footprints = []
ts_delays = []
for submit_date in submit_dates:
    ca_timetable = Timetable()
    # Append ground truth data to timetables (no forecasting error)
    ca_timetable.append_historic(
        start=submit_date, end=submit_date + timedelta(hours=24)
    )
    ts_timetable = Timetable()
    ts_timetable.append_historic(
        start=submit_date, end=submit_date + timedelta(hours=24)
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
    delays = []
    for index, slot in enumerate(ca_timetable.timeslots):
        if len(slot.reserved_resources) == 1:
            delays.append(index)
            ca_footprint += slot.gci * (JOB_CONSUMPTION_WATTS / 1000)
        elif len(slot.reserved_resources) > 1:
            raise RuntimeError(
                "Please use single-node configuration for this experiment!"
            )
    ca_footprints.append(round(ca_footprint, 2))
    ca_delays.append(np.average(delays))
    # Calculate timeshifting emissions and average delay
    ts_footprint = 0
    delays = []
    for index, slot in enumerate(ts_timetable.timeslots):
        if len(slot.reserved_resources) == 1:
            delays.append(index)
            ts_footprint += slot.gci * (JOB_CONSUMPTION_WATTS / 1000)
        elif len(slot.reserved_resources) > 1:
            raise RuntimeError(
                "Please use single-node configuration for this experiment!"
            )
    ts_footprints.append(round(ts_footprint, 2))
    ts_delays.append(np.average(delays))
hours = range(24)

# Plot sample
plt.step(
    submit_dates[SAMPLE_DAY_START * 24 : SAMPLE_DAY_END * 24],
    ca_footprints[SAMPLE_DAY_START * 24 : SAMPLE_DAY_END * 24],
    color="blue",
    label="FIFO",
)
plt.step(
    submit_dates[SAMPLE_DAY_START * 24 : SAMPLE_DAY_END * 24],
    ts_footprints[SAMPLE_DAY_START * 24 : SAMPLE_DAY_END * 24],
    color="orange",
    label="Timeshifting",
)
plt.xlabel("Hour of submission")
plt.xticks(rotation=45)
plt.ylabel("CO2-eq. emitted [g]")
plt.title("Carbon Footprint of Scenario A for 1-day ahead Scheduling")
plt.legend()
plt.tight_layout()
plt.savefig(RESULT_DIR / "exp1-sample.png")
plt.clf()

# Plot savings per hour of day
ts_savings_hourly_median = np.ma.median(
    np.subtract(1, np.divide(ts_footprints, ca_footprints)).reshape((DAYS, 24)), axis=0
)
plt.bar(hours, ts_savings_hourly_median, color="orange")
plt.xlabel("Hour of submission")
plt.ylabel("Median Fraction of Emissions Saved")
plt.ylim(0, 1)
plt.title("Median Fractional Carbon Savings for Scenario A (Timeshifting vs. FIFO)")
plt.tight_layout()
plt.savefig(RESULT_DIR / "exp1-results.png")
plt.clf()

# Plot average job delay
ts_hourly_delay = np.ma.median(np.reshape(ts_delays, (DAYS, 24)), axis=0)
ca_hourly_delay = np.ma.median(np.reshape(ts_delays, (DAYS, 24)), axis=0)
plt.plot(hours, ca_hourly_delay, color="blue", label="FIFO")
plt.plot(hours, ts_hourly_delay, color="orange", label="Timeshifting")
plt.ylabel("Avg. Delay [hours]")
plt.xlabel("Hour of submission")
