"""Persist state of scheduler on disk."""

from datetime import datetime, timedelta, UTC

from src.config.squirrel_conf import Config
from src.data.gci.influxdb import get_gci_data
from src.forecasting.gci import forecast_gci
from .timetable import Timetable, ConstrainedTimeslot


def load_timetable():
    latest = datetime.now(tz=UTC).replace(microsecond=0, second=0, minute=0)
    timetable = Timetable()
    timetable.read_csv(Config.get_local_paths()["schedule"])
    # timetable.truncate_history(start=latest)
    # TODO: Integrate forecast
    if len(timetable.timeslots) == 0:
        start_point = latest - timedelta(days=Config.get_lookback_days(), hours=1)
        gci_history = get_gci_data(start=start_point, stop=latest)
        forecast = forecast_gci(
            gci_history,
            days=Config.get_forecast_days(),
            lookback=Config.get_lookback_days(),
        )
        for _, row in forecast.iterrows():
            ts = ConstrainedTimeslot(
                start=row["time"],
                end=row["time"] + timedelta(hours=1),
                gci=row["gci"],
                jobs={},
                available_resources={"cpu": 1},
                reserved_resources={},
            )
            timetable.append_timeslot(ts)
    return timetable


def write_timetable(timetable: Timetable):
    timetable.write_csv(Config.get_local_paths()["schedule"])
