"""Retrieve energy data from the last year."""

from argparse import ArgumentParser
from datetime import timedelta, datetime, UTC
import json
from pathlib import Path

import requests
from tqdm import tqdm

RESULT_PATH = Path("research") / "data" / "energy-charts"
API_URL = "https://api.energy-charts.info/public_power"
TODAY = datetime.now(tz=UTC)


def _get_daily_public_power(country: str, timespan: int = 1) -> dict:
    result = {}

    for days in tqdm(range(0, timespan)):
        # Get the two days in the past
        time_delta_start = timedelta(days + 1)
        time_delta_end = timedelta(days)
        start_time = (TODAY - time_delta_start).strftime("%Y-%m-%d")
        end_time = (TODAY - time_delta_end).strftime("%Y-%m-%d")
        # Query the API and append response content to data
        url = f"{API_URL}?country={country}&start={start_time}&end={end_time}"
        response = requests.get(url, timeout=10)
        daily_public_power = response.json()
        result.update({start_time: daily_public_power})

    return result


def _get_public_power(country: str, timespan: int = 1) -> dict:
    # Get the two days in the past
    time_delta = timedelta(timespan)
    start_time = (TODAY - time_delta).strftime("%Y-%m-%d")
    end_time = TODAY.strftime("%Y-%m-%d")
    # Query the API and append response content to data
    url = f"{API_URL}?country={country}&start={start_time}&end={end_time}"
    response = requests.get(url, timeout=120)
    return response.json()


def _save_as_json(power_data: dict, country: str, timespan: int):
    file_name = f"{TODAY.strftime('%Y-%m-%d')}_{timespan}_({country}).json"
    result_file = RESULT_PATH / file_name
    RESULT_PATH.mkdir(exist_ok=True)
    file_content = json.dumps(power_data, indent=4, sort_keys=False)
    result_file.write_text(file_content, encoding="utf-8")


if __name__ == "__main__":
    argument_parser = ArgumentParser(
        prog="Get daily public power from Energy-Charts API."
    )
    argument_parser.add_argument(
        "--country",
        default="de",
        required=False,
        help="""Specify the country. Default: de.
            Available countries are listed here:
            https://api.energy-charts.info/""",
    )
    argument_parser.add_argument(
        "--days",
        default=1,
        required=False,
        help="Number of days to request. Default: 1",
    )
    argument_parser.add_argument(
        "--daily",
        action="store_true",
        help="Set if you want a result with days as keys.",
    )
    arguments = argument_parser.parse_args()

    if arguments.daily:
        public_power = _get_daily_public_power(
            country=arguments.country, timespan=int(arguments.days)
        )
    else:
        public_power = _get_public_power(
            country=arguments.country, timespan=int(arguments.days)
        )
    _save_as_json(
        power_data=public_power,
        country=arguments.country,
        timespan=int(arguments.days),
    )
