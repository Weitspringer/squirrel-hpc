"""Timeslot class"""

import csv
from datetime import datetime
import json
from pathlib import Path
from uuid import uuid4

TT_CSV_HEADER = ["start, end, gci, jobs, available_resources, reserved_resources"]


class ConstrainedTimeslot:
    """Timeslot with constraints."""

    def __init__(
        self,
        start: datetime,
        end: datetime,
        gci: float,
        jobs: dict,
        available_resources: dict,
        reserved_resources: dict,
    ) -> None:
        """Timeslot with constraints."""
        self.start = start
        self.end = end
        self.gci = gci
        self.jobs = jobs
        self.available_resources = available_resources
        self.reserved_resources = reserved_resources

    def get_duration(self):
        """Returns the duration of the time slot in seconds."""
        return (self.end - self.start).total_seconds()

    def get_gci(self):
        """Get the grid carbon intensity."""
        return self.gci

    def set_gci(self, gci: int):
        """Change the grid carbon intensity"""
        self.gci = gci

    def allocate_job(
        self, job_id: str, resources: dict, start: datetime, end: datetime
    ) -> str:
        """Request a certain amount of resources for a specified duration."""
        if (
            start >= self.start
            and end <= self.end
            and len(self.reserved_resources) == 0
        ):
            request_uuid = str(uuid4())
            self.reserved_resources.update(
                {
                    request_uuid: {
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "resources": resources,
                    }
                }
            )
            self.jobs.update({job_id: request_uuid})
            return request_uuid
        else:
            return None

    def is_full(self) -> bool:
        """Determine wether this timeslot is available or not."""
        return len(self.reserved_resources) != 0

    def remove_job(self, job_id: str) -> None:
        """Frees allocated resources."""
        res_id = self.jobs.pop(job_id)
        self.reserved_resources.pop(res_id)

    def __eq__(self, value: object) -> bool:
        """Defines when 2 time slots are equal."""
        if not isinstance(value, ConstrainedTimeslot):
            return False
        return self.start == value.start and self.end == value.end


class Timetable:
    """Container for timeslots."""

    def __init__(self, timeslots: list[ConstrainedTimeslot] = list()) -> None:
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
                        available_resources=json.loads(row[4]),
                        reserved_resources=json.loads(row[5]),
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
                        json.dumps(timeslot.available_resources),
                        json.dumps(timeslot.reserved_resources),
                    ]
                )