"""Scheduler for sbatch jobs."""

from datetime import datetime, UTC
from functools import reduce

from src.config.squirrel_conf import Config

from src.data.timetable.io import load_timetable, write_timetable
from .timetable import ConstrainedTimeslot, Timetable


def schedule_job(job_id: str, runtime: int, submit_date: datetime) -> datetime:
    """Schedule a job using runtime information.

    Runtime in hours.
    """
    timetable = load_timetable(latest_datetime=submit_date)
    timeslots = timetable.timeslots
    result = None
    if runtime / 24 < Config.get_forecast_days():
        # Find the window where the GCI impact is lowest.
        # NOTE: Jobs are assumed to be non-interruptible.
        fc_hours = len(timeslots)
        windows = {}
        for start_hour in range(0, fc_hours - runtime + 1):
            # Map-reduce to calculate weight of current window
            window = timeslots[start_hour : start_hour + runtime]
            window_gcis = list(map(lambda x: x.gci, window))
            weight = reduce(lambda x, y: x + y, window_gcis)
            windows.update({weight: window})
        result = _allocate_window_greedy(
            job_id=job_id, windows=windows, resources={}, timetable=timetable
        )
    write_timetable(timetable)
    if result:
        return result[0].start
    else:
        raise RuntimeError("Can not allocate job.")


def _allocate_window_greedy(
    job_id: str, windows: dict, resources: dict, timetable: Timetable
) -> list[ConstrainedTimeslot]:
    for _, window in dict(sorted(windows.items())).items():
        reserved_ts = []
        for timeslot in window:
            if timeslot.is_full():
                for ts in reserved_ts:
                    ts.remove_job(job_id)
                reserved_ts.clear()
                break
            res_id = timeslot.allocate_job(
                job_id=job_id,
                resources=resources,
                start=timeslot.start,
                end=timeslot.end,
            )
            if res_id:
                # Successful reservation of resources.
                reserved_ts.append(timeslot)
            else:
                # Reservation failed. Shift window to next one.
                for ts in reserved_ts:
                    ts.remove_job(job_id)
                reserved_ts.clear()
                break
        if len(reserved_ts) > 0:
            del reserved_ts
            return window
    return None
