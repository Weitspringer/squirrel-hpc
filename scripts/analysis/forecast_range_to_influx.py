from datetime import datetime, timedelta

import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data, write_gci_forecast
from src.forecasting.gci import builtin_forecast_gci

# Write forecast of multiple zones (for 2023) to InfluxDB.
fc_dates = pd.date_range(
    start=datetime.fromisoformat("2023-01-03T00:00+00:00"),
    periods=363,
    freq="d",
    tz="UTC",
)
zones = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
influx_opt_hist = Config.get_influx_config()["gci"]["history"]
influx_opt_fc = Config.get_influx_config()["gci"]["forecast"]
for zone in zones:
    influx_opt_hist.get("tags").update({"zone": zone})
    influx_opt_fc.get("tags").update({"zone": zone})
    for fc_date in fc_dates:
        gci_history = get_gci_data(
            start=fc_date - timedelta(days=2), stop=fc_date, options=influx_opt_hist
        )
        forecast = builtin_forecast_gci(
            gci_history,
            days=Config.get_forecast_days(),
            lookback=Config.get_lookback_days(),
        )
        write_gci_forecast(forecast=forecast, options=influx_opt_fc)
