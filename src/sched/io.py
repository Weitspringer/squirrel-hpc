import pandas as pd

from src.config.squirrel_conf import Config


def load_schedule():
    # TODO: Get real forecast, make rolling window
    return pd.read_csv(Config.get_local_paths()["schedule"])


def write_schedule(data: pd.DataFrame):
    data.to_csv(Config.get_local_paths()["schedule"], index=False)
