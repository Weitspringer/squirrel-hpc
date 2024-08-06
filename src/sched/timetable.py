"""Timetable"""

import csv
from datetime import datetime, timedelta
import json
from pathlib import Path

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data
from src.forecasting.gci import builtin_forecast_gci
from src.sched.timeslot import ConstrainedTimeslot

TT_CSV_HEADER = ["start, end, gci, jobs, reserved_resources"]


class Timetable:
    """Container for timeslots."""

    def __init__(
        self,
        timeslots: list[ConstrainedTimeslot] | None = list(),
    ) -> None:
        """Returns an empty time table."""
        self.timeslots = timeslots
        self._csv_header = TT_CSV_HEADER

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

    def append_forecast(self, start: datetime):
        """Append the forecast starting at a certain time."""
        fc_days = Config.get_forecast_days()
        start_point = start - timedelta(days=Config.get_lookback_days(), hours=1)
        gci_history = get_gci_data(start=start_point, stop=start)
        # TODO: Get forecast from InfluxDB
        forecast = builtin_forecast_gci(
            gci_history, days=fc_days, lookback=Config.get_lookback_days()
        )
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
        with open(csv_path, "r") as csv_file:
            ttreader = csv.reader(csv_file)
            ttreader.__next__()
            for row in ttreader:
                self.append_timeslot(
                    ConstrainedTimeslot(
                        start=datetime.fromisoformat(row[0]),
                        end=datetime.fromisoformat(row[1]),
                        gci=float(row[2]),
                        jobs=json.loads(row[3]),
                        reserved_resources=json.loads(row[4]),
                    )
                )

    def write_csv(self, csv_path: Path):
        """Writes state to csv file."""
        with open(csv_path, "w") as csv_file:
            ttwriter = csv.writer(csv_file)
            ttwriter.writerow(self._csv_header)
            for timeslot in self.timeslots:
                ttwriter.writerow(
                    [
                        timeslot.start.isoformat(),
                        timeslot.end.isoformat(),
                        timeslot.gci,
                        json.dumps(timeslot.jobs),
                        json.dumps(timeslot.reserved_resources),
                    ]
                )
