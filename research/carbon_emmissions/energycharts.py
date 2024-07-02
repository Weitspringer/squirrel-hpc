"""Calculate carbon intensity using data from Energy-Charts"""

from datetime import datetime

import matplotlib.pyplot as plt
import requests

from research.carbon_emmissions.coefficients import CO2E
from research.config import RE_CARBON
from research.utils.data import save_dict_as_json
from research.utils.time import get_timedeltas


def get_carbon_intensity(country: str, response: dict) -> dict:
    """Generate carbon intensity data using the country's coefficients
    and energy data from Energy-Charts API.
    """
    # Calculate carbon intensity [gCO2-eq./kWh]
    if CO2E.get(country):
        co2e_coeff = CO2E[country]
    else:
        print(f"Country '{country}' has no CO2e coefficients.")
        return None

    # Get lengths between timestamps
    timedeltas = get_timedeltas(
        unix_seconds=response["unix_seconds"], unit="minutes", extend_tail=True
    )

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

    return {
        "unix_seconds": response["unix_seconds"],
        "gco2eq_per_kwh": carbon_intensities,
    }


def generate_carbon_intensities(
    country: str,
    response: dict,
    end: datetime,
    timespan: int,
    compare_with_api: bool = True,
) -> dict:
    """Generates a plot to compare it to the Energy-Charts API result. Also stores the data.

    Args:
        country (str): Country code of location (must be available in Energy-Charts).
        response (dict): Response from public_power_public_power_get endpoint.
        end (datetime): Meta-information for file. Most recent day contained in data.
        timespan (int): Meta-information for filename. Amount of days contained in data.

    Returns:
        dict: Carbon intensity data.
    """

    carbon_intensities = get_carbon_intensity(country=country, response=response)

    save_dict_as_json(
        data=carbon_intensities,
        name=f"{end.strftime('%Y-%m-%d')}_{timespan}_({country})",
        folder_path=RE_CARBON,
    )

    if compare_with_api:
        # Get response from API for comparison
        timestamps = list(
            map(datetime.fromtimestamp, carbon_intensities["unix_seconds"])
        )
        _plot_data(
            country=country,
            timestamps=timestamps,
            carbon_intensities=carbon_intensities["gco2eq_per_kwh"],
        )

    return carbon_intensities


def _fetch_carbon_intensity(country: str, start: datetime, end: datetime) -> dict:
    """Get the carbon intensity as API response."""

    # Query the API
    date_fmt = "%Y-%m-%dT%H:%mZ"
    url = (
        "https://api.energy-charts.info/co2eq"
        f"?country={country}&start={start.strftime(date_fmt)}&end={end.strftime(date_fmt)}"
    )
    return requests.get(url, timeout=120).json()


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
