"""Timetable"""

from datetime import datetime, timedelta
import json
from pathlib import Path

import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data
from src.forecasting.gci import builtin_forecast_gci
from src.sched.timeslot import ConstrainedTimeslot


class Timetable:
    """Container for timeslots."""

    def __init__(
        self,
        timeslots: list[ConstrainedTimeslot] | None = None,
    ) -> None:
        """Returns an empty time table."""
        if timeslots:
            self.timeslots = timeslots
        else:
            self.timeslots = []

    def append_timeslot(self, timeslot: ConstrainedTimeslot) -> bool:
        """Append a timeslot to the latest timeslot.

        If there are already timeslots in the timetable,
        the start time of the appended time slot must match
        the end time of the last time slot.
        """
        if not self.is_empty() and self.timeslots[-1].end != timeslot.start:
            return False
        self.timeslots.append(timeslot)
        return True

    def is_empty(self) -> bool:
        """Check if there are timeslots in the timetable."""
        return len(self.timeslots) <= 0

    def get_latest(self) -> ConstrainedTimeslot:
        """Get the latest timeslot."""
        return self.timeslots[-1]

    def append_forecast(
        self,
        start: datetime,
        forecast_days: int,
        lookback_days: int,
        options: dict | None = None,
    ):
        """Append timeslots using the forecast starting at a certain time."""
        if Config.use_builtin_forecast():
            if not options:
                options = Config.get_influx_config()["gci"]["history"]
            start_point = start - timedelta(days=lookback_days, hours=1)
            try:
                gci_history = get_gci_data(start=start_point, stop=start, options=options)
            except ValueError:
                raise ValueError("Built-in forecasting: Not enough historical GCI data.")
            forecast = builtin_forecast_gci(
                gci_history, days=forecast_days, lookback=lookback_days
            )
        else:
            if not options:
                options = Config.get_influx_config()["gci"]["forecast"]
            try:
                forecast = get_gci_data(
                    start=start,
                    stop=start + timedelta(days=forecast_days),
                    options=options,
                )
            except ValueError:
                raise ValueError("No GCI forecast data in InfluxDB.")
        # Create new time slots
        for _, row in forecast.iterrows():
            ts = ConstrainedTimeslot(
                start=row["time"],
                end=row["time"] + timedelta(hours=1),
                gci=row["gci"],
                jobs={},
                reserved_resources={},
            )
            self.append_timeslot(ts)

    def append_historic(
        self, start: datetime, end: datetime, options: dict | None = None
    ):
        """Append timeslots using historical data."""
        gci_history = get_gci_data(start=start, stop=end, options=options)
        for _, row in gci_history.iterrows():
            ts = ConstrainedTimeslot(
                start=row["time"],
                end=row["time"] + timedelta(hours=1),
                gci=row["gci"],
                jobs={},
                reserved_resources={},
            )
            self.append_timeslot(ts)

    def append_direct(self, gci_data: pd.DataFrame):
        """Append timeslots using data from data frame."""
        for _, row in gci_data.iterrows():
            ts = ConstrainedTimeslot(
                start=row["time"],
                end=row["time"] + timedelta(hours=1),
                gci=row["gci"],
                jobs={},
                reserved_resources={},
            )
            self.append_timeslot(ts)

    def truncate_history(self, latest: datetime):
        """Discard timeslots from the past."""
        i = 0
        for timeslot in self.timeslots:
            if timeslot.end <= latest:
                i += 1
            else:
                break
        self.timeslots = self.timeslots[i:]

    def read_csv(self, csv_path: Path):
        """Reads state from csv file."""
        input_data = pd.read_csv(csv_path)
        for _, row in input_data.iterrows():
            self.append_timeslot(
                ConstrainedTimeslot(
                    start=datetime.fromisoformat(row["start"]),
                    end=datetime.fromisoformat(row["end"]),
                    gci=float(row["gci"]),
                    jobs=json.loads(row["jobs"]),
                    reserved_resources=json.loads(row["reserved_resources"]),
                )
            )

    def write_csv(self, csv_path: Path):
        """Writes state to csv file."""
        rows = []
        for timeslot in self.timeslots:
            rows.append(
                {
                    "start": timeslot.start.isoformat(),
                    "end": timeslot.end.isoformat(),
                    "gci": timeslot.gci,
                    "jobs": json.dumps(timeslot.jobs),
                    "reserved_resources": json.dumps(timeslot.reserved_resources),
                }
            )
        pd.DataFrame(rows).to_csv(csv_path)
