"""Timeshifting experiment."""

from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.sched.scheduler import Scheduler, TemporalShifting, CarbonAgnosticFifo
from src.sched.timetable import Timetable

DAYS = 5
JOB_CONSUMPTION_WATTS = 150
CLUSTER_PATH = Path("simulation") / "data" / "single-node-cluster.json"
# Create schedulers
carbon_agnostic_scheduler = Scheduler(
    strategy=CarbonAgnosticFifo(),
    cluster_info=CLUSTER_PATH,
)
timeshift_scheduler = Scheduler(strategy=TemporalShifting(), cluster_info=CLUSTER_PATH)
# Create date range
first_submit_date = datetime.fromisoformat("2023-08-02T00:00:00+00:00")
submit_dates = pd.date_range(
    start=first_submit_date,
    periods=DAYS * 24,
    freq="h",
    tz="UTC",
)
ca_footprints = []
ts_footprints = []
# Scheduling for multiple timetables
result_dir = Path("simulation") / "data" / "results"
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
    # Calculate carbon-agnostic emissions
    ca_footprint = 0
    for slot in ca_timetable.timeslots:
        if len(slot.reserved_resources) == 1:
            ca_footprint += slot.gci * (JOB_CONSUMPTION_WATTS / 1000)
        elif len(slot.reserved_resources) > 1:
            raise RuntimeError(
                "Please use single-node configuration for this experiment!"
            )
    ca_footprints.append(round(ca_footprint, 2))
    ts_footprint = 0
    for slot in ts_timetable.timeslots:
        if len(slot.reserved_resources) == 1:
            ts_footprint += slot.gci * (JOB_CONSUMPTION_WATTS / 1000)
        elif len(slot.reserved_resources) > 1:
            raise RuntimeError(
                "Please use single-node configuration for this experiment!"
            )
    ts_footprints.append(round(ts_footprint, 2))
plt.step(submit_dates, ca_footprints, color="grey", label="FIFO")
plt.step(submit_dates, ts_footprints, color="green", label="Timeshift")
plt.xticks(rotation=45)
plt.xlabel("Hour of submission")
plt.ylabel("gCO2-eq. emitted")
plt.title("Carbon Footprint of Scenario A for 1-day ahead Scheduling")
plt.legend()
plt.tight_layout()
plt.savefig(Path("viz") / "simulation" / "timeshift-effect-perfect-forecast.png")
