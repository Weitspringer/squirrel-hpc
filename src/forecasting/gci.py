"""GCI Forecasting"""

from datetime import timedelta

import numpy as np
import pandas as pd


def forecast_gci(data: pd.DataFrame, days: int = 1, lookback: int = 2) -> pd.DataFrame:
    """Forecast the grid carbon intensity for the next specified number of days.

    This function predicts the grid carbon intensity (GCI) for the upcoming days
    using a windowing method based on historical data. The forecast is made for
    each hour of the specified number of days, and each prediction is based on the
    median GCI values from the lookback period.

    Args:
        data (pd.DataFrame): A DataFrame containing historical data with columns "time"
            (datetime) and "gci" (grid carbon intensity).
        days (int, optional): The number of days to forecast. Defaults to 1.
        lookback (int, optional): The number of previous days to use for the lookback window. Defaults to 2.

    Returns:
        pd.DataFrame: A DataFrame containing the forecasted GCI with columns "time" and "gci".

    Example:
        data = pd.DataFrame({
            'time': pd.date_range(start='2022-01-01T00:00:00Z', periods=48, freq='H'),
            'gci': np.random.rand(48)
        })

        forecast(data, days=1, lookback=2)
    """
    latest_ts = data["time"].max()
    forecast_times = pd.date_range(
        start=latest_ts + timedelta(hours=1),
        periods=days * 24,
        freq="h",
        tz="UTC",
    )
    forecast = []
    for time_point in forecast_times:
        points = []
        for day_offset in range(1, lookback + 1):
            past_time_point = time_point - timedelta(days=day_offset)
            if past_time_point < latest_ts:
                points.append(data[data["time"] == past_time_point]["gci"].values[0])
            else:
                for fc_point in forecast:
                    if fc_point["time"] == past_time_point:
                        points.append(fc_point["gci"])
        forecast.append({"time": time_point, "gci": np.median(points)})
    return pd.DataFrame(forecast)
