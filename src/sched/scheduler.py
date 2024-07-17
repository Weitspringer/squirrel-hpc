"""Scheduler for sbatch jobs."""

from datetime import datetime
from functools import reduce

from src.config.squirrel_conf import Config

from .io import load_timetable, write_timetable
from .timetable import ConstrainedTimeslot


def schedule_job(job_id: str, runtime: int) -> datetime:
    """Schedule a job using runtime information.

    Runtime in hours.
    """
    timetable = load_timetable()
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
            job_id=job_id, windows=windows, resources={"cpu": 1}
        )
    write_timetable(timetable)
    if result:
        return result[0].start
    else:
        raise RuntimeError("Can not allocate job.")


def _allocate_window_greedy(
    job_id: str, windows: dict, resources: dict
) -> list[ConstrainedTimeslot]:
    for _, window in dict(sorted(windows.items())).items():
        reserved = {}
        for timeslot in window:
            res_id = timeslot.allocate_job(
                job_id=job_id,
                resources=resources,
                start=timeslot.start,
                end=timeslot.end,
            )
            if res_id:
                # Successful reservation of resources.
                reserved.update({job_id: timeslot})
            else:
                # Reservation failed. Shift window to next one.
                for key, ts in reserved.items():
                    ts.remove_job(key)
                reserved.clear()
                break
        if len(reserved) > 0:
            return window
    return None
