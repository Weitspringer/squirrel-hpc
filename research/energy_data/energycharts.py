"""Retrieve energy data from the last year."""

from argparse import ArgumentParser
from datetime import timedelta, datetime, UTC
import json
from pathlib import Path

import matplotlib.pyplot as plt
import requests

from research.energy_data.coefficients import CO2E, dummy

RESULT_PATH = Path("research") / "data" / "energy-charts"
API_URL = "https://api.energy-charts.info/public_power"
TODAY = datetime.now(tz=UTC)


def _get_public_power(country: str, timespan: int = 1) -> dict:
    # Get power generation in MW

    # Get the two days in the past
    time_delta = timedelta(timespan)
    start_time = (TODAY - time_delta).strftime("%Y-%m-%d")
    end_time = TODAY.strftime("%Y-%m-%d")
    # Query the API and append response content to data
    url = f"{API_URL}?country={country}&start={start_time}&end={end_time}"
    response = requests.get(url, timeout=120).json()

    # Calculate carbon intensity [CO2-eq./MWh]
    if CO2E.get(country):
        co2e_coeff = CO2E[country]
    else:
        print(f"Country '{country}' has no CO2-eq. coefficients.")
        return response
    minutes_between_datapoints = 15
    carbon_intensities = []
    for production_type in response["production_types"]:
        if production_type["name"] in co2e_coeff.keys():
            for index, prod_mw in enumerate(production_type["data"]):
                if len(carbon_intensities) < index + 1:
                    carbon_intensities.append(0)
                if prod_mw != "null":
                    carbon_intensities[index] += (
                        float(prod_mw)
                        * co2e_coeff[production_type["name"]]
                        * (minutes_between_datapoints / 60)
                    )
    plt.plot(carbon_intensities)
    plt.show()

    return response


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
    arguments = argument_parser.parse_args()

    public_power = _get_public_power(
        country=arguments.country, timespan=int(arguments.days)
    )
    _save_as_json(
        power_data=public_power,
        country=arguments.country,
        timespan=int(arguments.days),
    )
