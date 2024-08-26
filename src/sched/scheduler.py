from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from functools import reduce
from pathlib import Path

from src.cluster.commons import get_partitions, get_cpu_tdp, get_gpu_tdp
from .timetable import Timetable, ConstrainedTimeslot


class Scheduler:
    """
    Scheduler for Slurm workloads, allowing for different strategies using the
    Strategy pattern.
    """

    def __init__(self, strategy: PlanningStrategy, cluster_info: Path = None) -> None:
        """
        The scheduler accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._strategy = strategy
        self._cluster_info = cluster_info

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
        self,
        timetable: Timetable,
        job_id: str,
        hours: int,
        partitions: list[str],
    ) -> tuple[datetime, str]:
        """
        Delegates job scheduling to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """
        r_window = None
        if hours <= len(timetable.timeslots):
            nodes = self._get_nodeset(partitions=partitions)
            r_window, r_node = self._strategy.allocate_resources(
                job_id=job_id, hours=hours, timetable=timetable, nodes=nodes
            )
        if not r_window:
            raise RuntimeError("Can not allocate job.")
        return r_window[0].start, r_node

    def _get_nodeset(self, partitions: list[str]) -> list[str]:
        # Get suitable nodes based on partitions
        cluster = get_partitions(path_to_json=self._cluster_info)
        nodes = set()
        for partition, p_nodes in cluster.items():
            if partition in partitions:
                for p_node in p_nodes:
                    nodes.add(p_node["hostname"])
        return nodes


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
        hours: int,
        timetable: Timetable,
        nodes: list[str],
    ) -> tuple[list[ConstrainedTimeslot], str]:
        pass


class CarbonAgnosticFifo(PlanningStrategy):
    """Carbon-agnostic first-in-first-out (fifo) scheduling strategy."""

    def allocate_resources(
        self, job_id: str, hours: int, timetable: Timetable, nodes: list[str]
    ):
        timeslots = timetable.timeslots
        for start_hour in range(0, len(timeslots) - hours + 1):
            window = timeslots[start_hour : start_hour + hours]
            for node in nodes:
                reserved_ts = _reserve_resources(
                    job_id=job_id, window=window, node=node
                )
                if reserved_ts:
                    return window, node
        return None, None


class TemporalShifting(PlanningStrategy):
    """Carbon-aware temporal workload shifting."""

    def allocate_resources(
        self, job_id: str, hours: int, timetable: Timetable, nodes: list[str]
    ):
        timeslots = timetable.timeslots
        # Find the window where the GCI impact is lowest.
        # NOTE: Jobs are assumed to be non-interruptible.
        fc_hours = len(timeslots)
        windows = {}
        for start_hour in range(0, fc_hours - hours + 1):
            # Map-reduce to calculate weight of current window
            window = timeslots[start_hour : start_hour + hours]
            window_gcis = list(map(lambda x: x.gci, window))
            weight = reduce(lambda x, y: x + y, window_gcis)
            windows.update({weight: window})
        # Try to allocate window with low carbon intensity
        for _, window in dict(sorted(windows.items())).items():
            reserved_ts = []
            # Reserve a single node during the timespan
            for node in nodes:
                reserved_ts = _reserve_resources(
                    job_id=job_id, window=window, node=node
                )
                if reserved_ts:
                    return window, node
        return None, None


class SpatialShifting(PlanningStrategy):
    def allocate_resources(
        self, job_id: str, hours: int, timetable: Timetable, nodes: list[str]
    ):
        timeslots = timetable.timeslots
        # Try to allocate node with lowest TDP possible.
        nodes_and_tdp = {}
        for node in nodes:
            cpu_tdp = get_cpu_tdp(hostname=node)
            if cpu_tdp is not None:
                nodes_and_tdp.update({node: cpu_tdp})
        sorted_nodes = sorted(nodes_and_tdp.items(), key=lambda x: x[1])
        for i in range(len(sorted_nodes)):
            node, tdp = sorted_nodes[i]
            # Get distance to TDP of the next, worse option.
            distance_next_tdp = None
            if i < len(sorted_nodes) - 1:
                distance_next_tdp = sorted_nodes[i + 1][1] - tdp
            # Try to allocate a window of the current node for this job.
            for start_hour in range(0, len(timeslots) - hours + 1):
                window = timeslots[start_hour : start_hour + hours]
                reserved_ts = _reserve_resources(
                    job_id=job_id, window=window, node=node
                )
                if reserved_ts:
                    return window, node
                elif distance_next_tdp is not None:
                    # If there is an equally suitable node, try next node to reduce delay.
                    if distance_next_tdp == 0:
                        # TODO: Load balancing for nodes with equal TDP (otherwise, the distribution is not optimal)
                        break
                    # Resonably delay jobs with regards to potential savings through spatial shifting.
                    # Scales linear with amount of delay in hours compared to TDP difference to the next, worse option.
                    if distance_next_tdp / 10 < start_hour:
                        # TODO: Introduce offset to start this anew in case this "subwindow" is full.
                        break
        return None, None


def _reserve_resources(
    job_id: str, window: list[ConstrainedTimeslot], node: str
) -> list[str] | None:
    # Reserve resources for a whole window
    reserved_ts = []
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
        return reserved_ts
    return None
