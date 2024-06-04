"""Methods for estimating carbon emmissions and making said results more tangible."""

from research.utils.time import interpolate_by_minutes


def estimate_carbon_emmissions(
    power_w: list[int], gco2eq_per_kwh: list[int], unix_seconds: list[int]
) -> float:
    """Estimate the carbon emmissions

    Args:
        power_w (list[int]): Data points for power (in Watts).
        gco2eq_per_kwh (list[int]): Data points for carbon intensity (in gCO2-eq. / kWh).
        unix_seconds (list[int]): Timestamps (in unix seconds).

    Returns:
        float: Total amount of CO2-eq. emitted (in grams).
    """

    assert len(power_w) == len(
        gco2eq_per_kwh
    ), "Different amounts of energy and carbon data points"
    assert len(power_w) == len(unix_seconds), "Timestamps don't match data points"

    # Minute-wise resolution
    power_w_interp = interpolate_by_minutes(data=power_w, unix_seconds=unix_seconds)
    gco2eq_per_kwh_interp = interpolate_by_minutes(
        data=gco2eq_per_kwh, unix_seconds=unix_seconds
    )

    gco2eq = 0
    for index, power in enumerate(power_w_interp):
        power_kw = power / 1000
        kwh = power_kw * (1 / 60)  # because we have 1-minute resultion
        emmissions = kwh * gco2eq_per_kwh_interp[index]
        gco2eq += emmissions
    return gco2eq
