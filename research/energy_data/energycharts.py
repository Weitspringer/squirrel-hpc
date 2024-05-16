"""Retrieve energy data from the last year."""

from argparse import ArgumentParser
from datetime import timedelta, datetime, UTC
import json
from pathlib import Path

import matplotlib.pyplot as plt
import requests

from research.energy_data.coefficients import CO2E
from research.time.utils import get_timedeltas_in_minutes

RESULT_PATH = Path("research") / "data" / "energy-charts"
NOW = datetime.now(tz=UTC)


def get_public_power(country: str, start: datetime, end: datetime) -> dict:
    """Query Energy-Charts for the public power during the defined timespan.

    For more details see:
    https://api.energy-charts.info/#/power/public_power_public_power_get

    Args:
        country (str): Country for which you want the data.
        start (datetime): Start time in UTC.
        end (datetime): End time in UTC.

    Returns:
        dict: Response from API as JSON.
    """

    # Query the API
    date_fmt = "%Y-%m-%dT%H:%mZ"
    url = (
        "https://api.energy-charts.info/public_power"
        f"?country={country}&start={start.strftime(date_fmt)}&end={end.strftime(date_fmt)}"
    )
    return requests.get(url, timeout=120).json()


def _get_api_carbon_intensity(country: str, start: datetime, end: datetime) -> dict:

    # Query the API
    date_fmt = "%Y-%m-%dT%H:%mZ"
    url = (
        "https://api.energy-charts.info/co2eq"
        f"?country={country}&start={start.strftime(date_fmt)}&end={end.strftime(date_fmt)}"
    )
    return requests.get(url, timeout=120).json()


def _get_public_power(country: str, timespan: int = 1) -> dict:
    # Get power generation in MW

    time_delta = timedelta(timespan)
    start_time = NOW - time_delta
    response = get_public_power(country=country, start=start_time, end=NOW)

    _plot_and_compare_carbon_intensity(country=country, response=response)

    return response


def _plot_and_compare_carbon_intensity(country: str, response: dict):
    # Calculate carbon intensity [gCO2-eq./kWh]
    if CO2E.get(country):
        co2e_coeff = CO2E[country]
    else:
        print(f"Country '{country}' has no CO2e coefficients.")
        return

    # Get lengths between timestamps
    timedeltas = get_timedeltas_in_minutes(response["unix_seconds"])

    # Get amount of energy and emmissions produced during timeslots
    emmissions_produced = []
    energy_produced = []
    carbon_intensities = []
    for production_type in response["production_types"]:
        # Only use known energy sources
        if production_type["name"] in co2e_coeff.keys():
            # Get energy and emmissions produced for the current power source
            for index, prod_mw in enumerate(production_type["data"]):
                if len(emmissions_produced) < index + 1:
                    emmissions_produced.append(0)
                    energy_produced.append(0)
                if prod_mw != "null" and prod_mw is not None:
                    kwh_from_source = float(prod_mw) * timedeltas[index] * 1000
                    emmissions_produced[index] += (
                        kwh_from_source * co2e_coeff[production_type["name"]]
                    )
                    energy_produced[index] += kwh_from_source

    # Normalize emmissions produced by the amount of energy generated
    for index, emmissions in enumerate(emmissions_produced):
        if energy_produced[index] != 0:
            carbon_intensities.append(emmissions / energy_produced[index])
        else:
            carbon_intensities.append(0)

    # Get response from API
    timestamps = list(map(datetime.fromtimestamp, response["unix_seconds"]))
    api_ci = _get_api_carbon_intensity(
        country=country, start=timestamps[0], end=timestamps[-1]
    )
    api_ts = list(map(datetime.fromtimestamp, api_ci["unix_seconds"]))

    plt.ylabel("Carbon Intensity [gCO2e / kWh]")
    plt.title(f"Grid Carbon Intensity [{country}]")
    plt.plot(timestamps, carbon_intensities, label="Squirrel")
    plt.plot(api_ts, api_ci["co2eq"], label="Energy-Charts")
    plt.gcf().autofmt_xdate()
    plt.legend()
    plt.show()


def _save_as_json(power_data: dict, country: str, timespan: int):
    file_name = f"{NOW.strftime('%Y-%m-%d')}_{timespan}_({country}).json"
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
    arguments = argument_parser.parse_args()

    public_power = _get_public_power(
        country=arguments.country, timespan=int(arguments.days)
    )
    _save_as_json(
        power_data=public_power,
        country=arguments.country,
        timespan=int(arguments.days),
    )
