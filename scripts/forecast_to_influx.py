from datetime import datetime, timedelta, UTC

from src.config.squirrel_conf import Config
from src.data.gci.influxdb import get_gci_data
from src.forecasting.gci import forecast_gci

end_point = datetime.now(tz=UTC).replace(microsecond=0, second=0, minute=0)
fc_settings = Config.get_builtin_forecast_config()
start_point = end_point - timedelta(days=fc_settings["lookback_days"], hours=1)
gci_history = get_gci_data(start=start_point, stop=end_point)
forecast = forecast_gci(
    gci_history,
    days=fc_settings["forecast_days"],
    lookback=fc_settings["lookback_days"],
)
