"""Persist state of scheduler on disk."""

from datetime import datetime, timedelta

from src.config.squirrel_conf import Config
from src.data.gci.influxdb import get_gci_data
from src.forecasting.gci import builtin_forecast_gci
from .timetable import Timetable, ConstrainedTimeslot


def load_timetable(latest_datetime: datetime) -> Timetable:
    """Load time table from CSV file, and guarantee that it contains a
    forecast starting at the latest datetime.

    Args:
        latest_datetime (datetime): Cutoff for forecast (e.g. now).

    Returns:
        Timetable: Timetable object containing timeslots with their states.
    """
    latest_datetime.replace(microsecond=0, second=0, minute=0)
    timetable = Timetable()
    timetable.read_csv(Config.get_local_paths()["schedule"])
    timetable.truncate_history(latest=latest_datetime)
    fc_days = Config.get_forecast_days()
    if len(timetable.timeslots) < fc_days * 24:
        start_point = latest_datetime - timedelta(
            days=Config.get_lookback_days(), hours=1
        )
        gci_history = get_gci_data(start=start_point, stop=latest_datetime)
        forecast = builtin_forecast_gci(
            gci_history, days=fc_days, lookback=Config.get_lookback_days()
        )
        for _, row in forecast.iterrows():
            ts = ConstrainedTimeslot(
                start=row["time"],
                end=row["time"] + timedelta(hours=1),
                gci=row["gci"],
                jobs={},
                available_resources={},
                reserved_resources={},
            )
            timetable.append_timeslot(ts)
    return timetable


def write_timetable(timetable: Timetable):
    """Write the state of a timetable to a .csv file.

    Args:
        timetable (Timetable): Timetable object to persist.
    """
    timetable.write_csv(Config.get_local_paths()["schedule"])
