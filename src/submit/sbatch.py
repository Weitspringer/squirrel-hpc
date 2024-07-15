"""Submit sbatch jobs"""

from datetime import datetime, timedelta, UTC
from heapq import heappush, heappop

from src.data.gci.influxdb import get_gci_data
from src.forecasting.gci import forecast_gci
from src.sched.timeslot import ConstrainedTimeslot


def submit_sbatch(command: str, runtime: int):
    end_point = datetime.now(tz=UTC).replace(microsecond=0, second=0, minute=0)
    start_point = end_point - timedelta(days=2, hours=1)
    gci_history = get_gci_data(start=start_point, stop=end_point)
    forecast = forecast_gci(gci_history, days=1, lookback=2)
    timeslot_heap = []
    for _, fc_item in forecast.iterrows():
        ts_item = ConstrainedTimeslot(
            fc_item["time"],
            fc_item["time"] + timedelta(hours=1),
            capacity=1,
            g_co2eq_per_kwh=fc_item["gci"],
        )
        heappush(
            timeslot_heap,
            ts_item,
        )
    best_ts = heappop(timeslot_heap)
