from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from functools import reduce

from src.cluster.commons import get_partitions
from src.config.squirrel_conf import Config
from src.data.timetable.io import load_timetable, write_timetable
from .timetable import ConstrainedTimeslot


class Scheduler:
    """
    Scheduler for Slurm workloads, allowing for different strategies using the
    Strategy pattern.
    """

    def __init__(self, strategy: PlanningStrategy) -> None:
        """
        The scheduler accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._strategy = strategy

    @property
    def strategy(self) -> PlanningStrategy:
        """
        Reference to one of the PlanningStrategy objects.
        """

        return self._strategy

    @strategy.setter
    def strategy(self, strategy: PlanningStrategy) -> None:
        """
        Replace a PlanningStrategy object at runtime.
        """

        self._strategy = strategy

    def schedule_sbatch(
        self, job_id: str, runtime: int, submit_date: datetime, partitions: list[str]
    ) -> tuple[datetime, str]:
        """
        Delegates job scheduling to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """
        timetable = load_timetable(latest_datetime=submit_date)
        timeslots = timetable.timeslots
        r_window = None
        if runtime / 24 <= Config.get_forecast_days():
            # Find the window where the GCI impact is lowest.
            # NOTE: Jobs are assumed to be non-interruptible.
            fc_hours = len(timeslots)
            windows = {}
            for start_hour in range(0, fc_hours - runtime + 1):
                # Map-reduce to calculate weight of current window
                window = timeslots[start_hour : start_hour + runtime]
                window_gcis = list(map(lambda x: x.gci, window))
                weight = reduce(lambda x, y: x + y, window_gcis)
                windows.update({weight: window})
            r_window, r_node = self._strategy.allocate_resources(
                job_id=job_id, windows=windows, partitions=partitions
            )
        write_timetable(timetable)
        if r_window:
            return r_window[0].start, r_node
        else:
            raise RuntimeError("Can not allocate job.")


class PlanningStrategy(ABC):
    """
    The PlanningStrategy interface declares operations common to all supported versions
    of algorithms for scheduling workloads.

    The scheduler uses this interface to call the algorithm defined by concrete
    strategies.
    """

    @abstractmethod
    def allocate_resources(
        self,
        job_id: str,
        windows: dict[float, list[ConstrainedTimeslot]],
        partitions: list[str],
    ):
        pass


class CarbonAgnosticFifo(PlanningStrategy):
    """Carbon-agnostic first-in-first-out (fifo) scheduling strategy."""

    def allocate_resources(
        self,
        job_id: str,
        windows: dict[float, list[ConstrainedTimeslot]],
        partitions: list[str],
    ) -> tuple[list[ConstrainedTimeslot], str]:
        raise NotImplementedError("Carbon-agnostic FIFO not implemented.")


class TemporalShifting(PlanningStrategy):
    """Carbon-aware temporal workload shifting."""

    def allocate_resources(
        self,
        job_id: str,
        windows: dict[float, list[ConstrainedTimeslot]],
        partitions: list[str],
    ) -> tuple[list[ConstrainedTimeslot], str]:
        # Get suitable nodes
        sinfo_json = Config.get_local_paths().get("sinfo_json")
        cluster = get_partitions(path_to_json=sinfo_json)
        nodes = set()
        for partition, p_nodes in cluster.items():
            if partition in partitions:
                for p_node in p_nodes:
                    nodes.add(p_node["hostname"])
        # Sort nodes descending with regards to their carbon intensity and iterate over them
        for _, window in dict(sorted(windows.items())).items():
            reserved_ts = []
            # Try to reserve a single node during the timespan
            for node in nodes:
                for timeslot in window:
                    if timeslot.is_full():
                        for ts in reserved_ts:
                            ts.remove_job(job_id)
                        reserved_ts.clear()
                        break

                    res_id = timeslot.allocate_node_exclusive(
                        job_id=job_id,
                        node_name=node,
                        start=timeslot.start,
                        end=timeslot.end,
                    )
                    if res_id:
                        # Successful reservation of resources.
                        reserved_ts.append(timeslot)
                    else:
                        # Reservation failed. Shift window to next one.
                        for ts in reserved_ts:
                            ts.remove_job(job_id)
                        reserved_ts.clear()
                        break
                if len(reserved_ts) > 0:
                    del reserved_ts
                    return window, node
        return None, None
