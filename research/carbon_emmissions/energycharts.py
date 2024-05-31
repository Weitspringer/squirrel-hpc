"""Calculate carbon intensity using data from Energy-Charts"""

from datetime import datetime

import matplotlib.pyplot as plt
import requests

from research.carbon_emmissions.coefficients import CO2E
from research.config import RE_CARBON
from research.utils.data import save_dict_as_json
from research.utils.time import get_timedeltas_in_minutes


def _fetch_carbon_intensity(country: str, start: datetime, end: datetime) -> dict:
    """Get the carbon intensity as API response."""

    # Query the API
    date_fmt = "%Y-%m-%dT%H:%mZ"
    url = (
        "https://api.energy-charts.info/co2eq"
        f"?country={country}&start={start.strftime(date_fmt)}&end={end.strftime(date_fmt)}"
    )
    return requests.get(url, timeout=120).json()


def generate_carbon_intensity_data(
    country: str, response: dict, end: datetime, timespan: int
) -> dict:
    """Generate carbon intensity data using the countrie's coefficients
    and energy data from Energy-Charts API.
    Also generates a plot to compare it to the Energy-Charts API result.

    Args:
        country (str): Country code of location (must be available in Energy-Charts).
        response (dict): Response from public_power_public_power_get endpoint.
        end (datetime): Meta-information for file. Most recent day contained in data.
        timespan (int): Meta-information for filename. Amount of days contained in data.

    Returns:
        dict: Carbon intensity data.
    """
    # Calculate carbon intensity [gCO2-eq./kWh]
    if CO2E.get(country):
        co2e_coeff = CO2E[country]
    else:
        print(f"Country '{country}' has no CO2e coefficients.")
        return None

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
                    kw_from_source = float(prod_mw) * timedeltas[index] * 1000
                    energy_produced[index] += kw_from_source
                    emmissions_produced[index] += (
                        kw_from_source * co2e_coeff[production_type["name"]]
                    )

    # Normalize emmissions produced by the amount of energy generated
    for index, emmissions in enumerate(emmissions_produced):
        if energy_produced[index] != 0:
            carbon_intensities.append(emmissions / energy_produced[index])
        else:
            carbon_intensities.append(0)

    carbon_intensity_data = {
        "unix_seconds": response["unix_seconds"],
        "data": carbon_intensities,
    }
    save_dict_as_json(
        data=carbon_intensity_data,
        name=f"{end.strftime('%Y-%m-%d')}_{timespan}_({country})",
        folder_path=RE_CARBON,
    )

    # Get response from API
    timestamps = list(map(datetime.fromtimestamp, response["unix_seconds"]))
    _plot_data(
        country=country, timestamps=timestamps, carbon_intensities=carbon_intensities
    )

    return carbon_intensity_data


def _plot_data(
    country: str, timestamps: list[datetime], carbon_intensities: list[float]
):
    """Compare with API response and plot."""
    api_ci = _fetch_carbon_intensity(
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
