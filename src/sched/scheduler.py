"""Scheduler for sbatch jobs."""

from functools import reduce

import pandas as pd

from src.config.squirrel_conf import Config

from .io import load_schedule, write_schedule


def schedule_job(runtime: int) -> pd.DataFrame:
    """Schedule a job using runtime information.

    Runtime in hours.
    """
    schedule = load_schedule()

    if runtime / 24 < Config.get_forecast_days():
        # Find the window where the GCI impact is lowest.
        # NOTE: Jobs are assumed to be non-interruptible.
        fc_hours = schedule.shape[0]
        min = None
        for start_hour in range(0, fc_hours - runtime + 1):
            # Map-reduce to calculate weight of current window
            window = schedule.iloc[list(range(start_hour, start_hour + runtime))]
            weight = reduce(
                lambda x, y: x + y,
                window["gci"],
            )
            # Compare with minimum so far
            if min is None or weight < min:
                min = weight
                result = schedule.iloc[[start_hour]]
    else:
        result = schedule.iloc[[-1]]
    write_schedule(schedule)
    return result
