"""Retrieve energy data from the last year."""

from argparse import ArgumentParser
from datetime import timedelta, datetime, UTC

import requests

from research.carbon_emmissions.energycharts import generate_carbon_intensity_data
from research.config import RE_ENERGY
from research.utils.data import save_dict_as_json


def get_public_power(country: str, end: datetime, timespan: int = 1) -> dict:
    """Get public power produced by various energy sources.

    Args:
        country (str): Location.
        end (datetime): Most recent datetime for request.
        timespan (int, optional): Timerange for request. Defaults to 1.

    Returns:
        dict: API response.
    """
    # Get power generation in MW

    time_delta = timedelta(timespan)
    start_time = end - time_delta
    response = _fetch_public_power(country=country, start=start_time, end=end)

    save_dict_as_json(
        data=response,
        name=f"{end.strftime("%Y-%m-%d")}_{int(timespan)}_({country})",
        folder_path=RE_ENERGY,
    )

    return response


def _fetch_public_power(country: str, start: datetime, end: datetime) -> dict:
    """Query Energy-Charts for the public power during the defined timespan.

    For more details see:
    https://api.energy-charts.info/#/power/public_power_public_power_get

    Args:
        country (str): Country for which you want the data.
        start (datetime): Start time in UTC.
        end (datetime): End time in UTC.

    Returns:
        dict: Response from API.
    """

    # Query the API
    date_fmt = "%Y-%m-%dT%H:%mZ"
    url = (
        "https://api.energy-charts.info/public_power"
        f"?country={country}&start={start.strftime(date_fmt)}&end={end.strftime(date_fmt)}"
    )
    return requests.get(url, timeout=120).json()


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
    arguments = argument_parser.parse_args()

    NOW = datetime.now(tz=UTC)
    public_power = get_public_power(
        country=arguments.country, timespan=int(arguments.days), end=NOW
    )
    generate_carbon_intensity_data(
        country=arguments.country,
        response=public_power,
        end=NOW,
        timespan=int(arguments.days),
    )
