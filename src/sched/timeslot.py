"""Timeslot class"""

from datetime import datetime


class ConstrainedTimeslot:
    def __init__(
        self,
        start: datetime,
        end: datetime,
        capacity: float,
        g_co2eq_per_kwh: float = None,
    ) -> None:
        """Timeslot for Squirrel

        Args:
            start (datetime): Start of the time slot.
            end (datetime): End of the time slot.
            capacity (float): Resources available in the time slot (in percent). Between 0 and 1.
            g_co2eq_per_kwh (float, optional): Grid carbon intensity during the given time. Defaults to None.
        """
        self.start = start
        self.end = end
        if capacity <= 1 and capacity >= 0:
            self.capacity = capacity
        else:
            raise ValueError("Capacity percentage has to be between 0 and 1.")
        self.g_co2eq_per_kwh = g_co2eq_per_kwh

    def set_capacity(self, capacity: float):
        """Update available resources percentage."""
        if capacity <= 1 and capacity >= 0:
            self.capacity = capacity
        else:
            raise ValueError("Capacity percentage has to be between 0 and 1.")

    def get_capacity(self):
        """Get the currently available resources as percentage."""
        return self.capacity

    def set_gci(self, g_co2eq_per_kwh: float):
        """Update the grid carbon intensity of the timeslot."""
        self.g_co2eq_per_kwh = g_co2eq_per_kwh

    def get_gci(self):
        """Get the current grid carbon intensity."""
        return self.g_co2eq_per_kwh

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ConstrainedTimeslot):
            return False
        return (self.end - self.start).total_seconds() * self.g_co2eq_per_kwh == (
            value.end - value.start
        ).total_seconds() * value.g_co2eq_per_kwh

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, ConstrainedTimeslot):
            raise NotImplementedError
        return (self.end - self.start).total_seconds() * self.g_co2eq_per_kwh < (
            value.end - value.start
        ).total_seconds() * value.g_co2eq_per_kwh
