"""Time utility functions"""

from datetime import datetime
from typing import Literal

import numpy as np


def get_timedeltas(
    unix_seconds: list[int],
    unit: Literal["days", "hours", "minutes", "seconds"] = "minutes",
    extend_tail: bool = False,
) -> list[float]:
    """Get the time differences between unix timestamps.
    Uses UTC timezone during calculation.

    Args:
        unix_timestamps (list[int]): List of unix timestamps.

        unit (Literal["days", "hours", "minutes", "seconds"], optional):
        Timedelta unit. Defaults to "minutes".

        extend_tail: (bool, optional): Assume the time slot for the last timestamp
        is the same as for second-to-last. Then, the length of the delta list
        is the length of the input timestamps.

    Returns:
        list[float]: List with timedeltas
    """
    timedeltas = []
    for index, timestamp in enumerate(unix_seconds):
        start = datetime.fromtimestamp(timestamp)
        if index == len(unix_seconds) - 1:
            if extend_tail:
                delta = timedeltas[-1]
            else:
                break
        else:
            end = datetime.fromtimestamp(unix_seconds[index + 1])
            difference = end - start
            match unit:
                case "days":
                    delta = difference.seconds / 60 / 60 / 24
                case "hours":
                    delta = difference.seconds / 60 / 60
                case "minutes":
                    delta = difference.seconds / 60
                case "seconds":
                    delta = difference.seconds
        timedeltas.append(float(delta))
    return timedeltas


def interpolate_by_minutes(data: list, unix_seconds: list[int], minutes: int = 1):
    """Interpolate data linearly by a given amount of minutes.

    Args:
        data (list): Data points.
        unix_seconds (list[int]): Timestamps of data points in unix seconds.
        minutes (int, optional): Resolution of interpolation in minutes. Defaults to 1.

    Returns:
        NDArray[float64]
    """
    x = np.arange(unix_seconds[0], unix_seconds[-1], step=minutes * 60)
    return np.interp(x=x, xp=unix_seconds, fp=data)
