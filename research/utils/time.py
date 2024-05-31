"""Time utility functions"""

from datetime import datetime


def get_timedeltas_in_minutes(unix_timestamps: list[int]):
    """Get the time differences between unix timestamps.
    Assumes that last slot is also as large as second-to-last.
    Uses UTC timezone during calculation.

    Args:
        unix_timestamps (list[int]): List of unix timestamps.
    """
    timedeltas = []
    for index, timestamp in enumerate(unix_timestamps):
        start = datetime.fromtimestamp(timestamp)
        if index < len(unix_timestamps) - 1:
            end = datetime.fromtimestamp(unix_timestamps[index + 1])
            difference = end - start
            timedeltas.append(difference.seconds / 60)
        else:
            timedeltas.append(timedeltas[index - 1])
    return timedeltas
