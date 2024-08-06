from datetime import datetime, timedelta, UTC

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data, write_gci_forecast
from src.forecasting.gci import builtin_forecast_gci

now = datetime.now(tz=UTC)
start_point = now - timedelta(days=Config.get_lookback_days(), hours=1)
gci_history = get_gci_data(start=start_point, stop=now)
forecast = builtin_forecast_gci(
    gci_history, days=Config.get_forecast_days(), lookback=Config.get_lookback_days()
)
write_gci_forecast(forecast=forecast)
