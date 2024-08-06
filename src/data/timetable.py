"""Persist state of scheduler on disk."""

import csv
from datetime import datetime, timedelta

from src.config.squirrel_conf import Config
from src.sched.timetable import Timetable


def tt_from_csv(start: datetime) -> Timetable | None:
    timetable = Timetable()
    schedule_path = Config.get_local_paths().get("schedule")
    # Check csv
    if not schedule_path.exists():
        return None
    # Load state from csv
    timetable.read_csv(schedule_path)
    # Remove past time points from time table
    timetable.truncate_history(latest=start + timedelta(hours=1))
    # Get forecast data if necessary
    timetable.append_forecast(start=start)
    return timetable


def tt_to_csv(timetable: Timetable):
    timetable.write_csv(Config.get_local_paths()["schedule"])
