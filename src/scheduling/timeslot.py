"""Timeslot class"""

from datetime import datetime


class SquirrelTimeslot:
    def __init__(
        self,
        start: datetime,
        end: datetime,
        capacity: dict,
        g_co2eq_per_kWh: float = None,
    ) -> None:
        """Timeslot for Squirrel

        Args:
            start (datetime): Start of the time slot.
            end (datetime): End of the time slot.
            capacity (dict): Resources available in the time slot.
            g_co2eq_per_kWh (float, optional): Grid carbon intensity during the given time. Defaults to None.
        """
        self.start = start
        self.end = end
        self.capacity = capacity
        self.g_co2eq_per_kWh = g_co2eq_per_kWh

    def set_capacity(self, capacity: dict):
        """Update available resources."""
        self.capacity = capacity

    def get_capacity(self):
        """Get the currently available resources."""
        return self.capacity.copy()

    def set_gci(self, g_co2eq_per_kWh: float):
        """Update the grid carbon intensity of the timeslot."""
        self.g_co2eq_per_kWh = g_co2eq_per_kWh

    def get_gci(self):
        """Get the current grid carbon intensity."""
        return self.g_co2eq_per_kWh
