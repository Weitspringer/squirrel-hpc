"""Persist state of scheduler on disk."""

import csv
from datetime import datetime, timedelta

from src.config.squirrel_conf import Config
from src.data.gci.influxdb import get_gci_data
from src.forecasting.gci import builtin_forecast_gci
from src.sched.timetable import Timetable, ConstrainedTimeslot, TT_CSV_HEADER


def load_timetable(latest_datetime: datetime) -> Timetable:
    """Load time table from CSV file, and guarantee that it contains a
    forecast starting at the latest datetime.

    Args:
        latest_datetime (datetime): Cutoff for forecast (e.g. now).

    Returns:
        Timetable: Timetable object containing timeslots with their states.
    """
    timetable = Timetable()
    # Check csv
    schedule_path = Config.get_local_paths().get("schedule")
    if not schedule_path.exists():
        with open(schedule_path, "w") as csv_file:
            ttwriter = csv.writer(csv_file)
            ttwriter.writerow(TT_CSV_HEADER)
    # Load state from csv
    timetable.read_csv(schedule_path)
    # Remove past time points from time table
    timetable.truncate_history(latest=latest_datetime)
    # Get forecast data if necessary
    fc_days = Config.get_forecast_days()
    if len(timetable.timeslots) < fc_days * 24:
        start_point = latest_datetime - timedelta(
            days=Config.get_lookback_days(), hours=1
        )
        gci_history = get_gci_data(start=start_point, stop=latest_datetime)
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
            timetable.append_timeslot(ts)
    return timetable


def write_timetable(timetable: Timetable):
    """Write the state of a time table to a .csv file.

    Args:
        timetable (Timetable): Timetable object to persist.
    """
    timetable.write_csv(Config.get_local_paths()["schedule"])
