from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from functools import reduce
from pathlib import Path

from src.cluster.commons import get_partitions, get_cpu_tdp, get_gpu_tdp
from src.errors.scheduling import (
    NoWindowAllocatedException,
    NoSuitableNodeException,
    JobTooLongException,
)
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
        num_gpus: int | None = None,
        gpu_name: str | None = None,
    ) -> tuple[datetime, str]:
        """
        Delegates job scheduling to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """
        r_window = None
        uses_gpu = num_gpus is not None
        if hours <= len(timetable.timeslots):
            nodes = self._get_nodeset(
                partitions=partitions, num_gpus=num_gpus, gpu_name=gpu_name
            )
            if len(nodes) == 0:
                raise NoSuitableNodeException(
                    "There is no node which satifies the GPU requirements."
                )
            r_window, r_node = self._strategy.allocate_resources(
                job_id=job_id,
                hours=hours,
                timetable=timetable,
                nodes=nodes,
                uses_gpu=uses_gpu,
            )
        else:
            raise JobTooLongException(
                f"You requested {hours} hours. The maximum amount is {len(timetable.timeslots)} hours."
            )
        if not r_window:
            raise NoWindowAllocatedException("The schedule is full.")
        return r_window[0].start, r_node

    def _get_nodeset(
        self,
        partitions: list[str],
        num_gpus: int | None = None,
        gpu_name: str | None = None,
    ) -> list[str]:
        # Get suitable nodes based on partitions and requested GPUs
        cluster = get_partitions(path_to_json=self._cluster_info)
        nodes = set()
        for partition, p_nodes in cluster.items():
            # Filter partitions
            if partition in partitions:
                for p_node in p_nodes:
                    # Analyze generic resources of node
                    if not self._gres_matches(p_node["gres"], num_gpus, gpu_name):
                        continue
                    nodes.add(p_node["hostname"])
        return nodes

    def _gres_matches(
        self, gres: str, num_gpus: int | None, gpu_name: str | None
    ) -> bool:
        """Check generic resource string and if the requirements are met."""
        if num_gpus:
            if gres == "":
                return False
            gres_list = gres.split(",")
            for gres_item in gres_list:
                gres_type = gres_item.split(":")[0]
                # Check if GPUs can be reserved
                if gres_type == "gpu":
                    gres_number = int(gres_item.split(":")[2].split("(")[0])
                    if gres_number >= num_gpus:
                        # If user provided GPU name, gres name must match
                        if gpu_name:
                            gres_name = gres_item.split(":")[1]
                            if gres_name != gpu_name:
                                continue
                        return True
            return False
        return True


class PlanningStrategy(ABC):
    """
    The PlanningStrategy interface declares operations common to all supported versions
    of algorithms for scheduling workloads.

    The scheduler uses this interface to call the algorithm defined by concrete
    strategies.
    """

    # NOTE: Jobs are assumed to be non-interruptible.

    @abstractmethod
    def allocate_resources(
        self,
        job_id: str,
        hours: int,
        timetable: Timetable,
        nodes: list[str],
        uses_gpu: bool,
    ) -> tuple[list[ConstrainedTimeslot], str]:
        """Exclusively allocate nodes for consecutive window in the timetable.
        The length of the window is determined by the specified hours.
        """
        pass


class CarbonAgnosticFifo(PlanningStrategy):
    """Carbon-agnostic first-in-first-out (fifo) scheduling strategy."""

    def allocate_resources(
        self,
        job_id: str,
        hours: int,
        timetable: Timetable,
        nodes: list[str],
        uses_gpu: bool,
    ) -> tuple[list[ConstrainedTimeslot], str]:
        timeslots = timetable.timeslots
        # Iterate through timetable (sliding window)
        for start_hour in range(0, len(timeslots) - hours + 1):
            window = timeslots[start_hour : start_hour + hours]
            # Skip window if there is a full slot in it
            full_slots = list(filter(lambda x: x.is_full(), window))
            if len(full_slots) > 0:
                continue
            # Try to reserve a node within the window
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
        self,
        job_id: str,
        hours: int,
        timetable: Timetable,
        nodes: list[str],
        uses_gpu: bool,
    ) -> tuple[list[ConstrainedTimeslot], str]:
        timeslots = timetable.timeslots
        # Find the window where the GCI impact is lowest.
        fc_hours = len(timeslots)
        weighted_windows = {}
        # Iterate through timetable (sliding window)
        for start_hour in range(0, fc_hours - hours + 1):
            # Map-reduce to calculate weight of current window
            window = timeslots[start_hour : start_hour + hours]
            # Skip window if there is a full slot in it
            full_slots = list(filter(lambda x: x.is_full(), window))
            if len(full_slots) > 0:
                continue
            # Calculate weight of window
            window_gcis = list(map(lambda x: x.gci, window))
            weight = reduce(lambda x, y: x + y, window_gcis)
            weighted_windows.update({weight: window})
        # Greedily allocate window with low carbon intensity
        for _, window in dict(sorted(weighted_windows.items())).items():
            reserved_ts = []
            # Reserve a single node during the timespan
            for node in nodes:
                reserved_ts = _reserve_resources(
                    job_id=job_id, window=window, node=node
                )
                if reserved_ts:
                    return window, node
        return None, None


class SpatialGreedyShifting(PlanningStrategy):
    def allocate_resources(
        self,
        job_id: str,
        hours: int,
        timetable: Timetable,
        nodes: list[str],
        uses_gpu: bool,
    ) -> tuple[list[ConstrainedTimeslot], str]:
        """Allocate node considering its TDP values. Greedy version."""

        # Extract the available timeslots from the timetable.
        timeslots = timetable.timeslots

        # Initialize dictionaries and lists to categorize nodes:
        # 'cpu_tdp_box' will store nodes with their corresponding TDP values.
        # 'blackbox' will store nodes without TDP information.
        cpu_tdp_box = {}
        blackbox = []
        for node in nodes:
            cpu_tdp = get_cpu_tdp(hostname=node)
            if cpu_tdp is not None:
                cpu_tdp_box.update({node: cpu_tdp})
            else:
                blackbox.append(node)

        # Sort nodes in 'cpu_tdp_box' by their TDP values in ascending order.
        sorted_nodes = sorted(cpu_tdp_box.items(), key=lambda x: x[1])
        # Try to allocate resources greedy for "best" node
        for i in range(len(sorted_nodes)):
            node, _ = sorted_nodes[i]
            for start_hour in range(0, len(timeslots) - hours + 1):
                window = timeslots[start_hour : start_hour + hours]
                # Skip window if there is a full slot in it
                full_slots = list(filter(lambda x: x.is_full(), window))
                if len(full_slots) > 0:
                    continue
                reserved_ts = _reserve_resources(
                    job_id=job_id, window=window, node=node
                )
                # If resources are successfully reserved, return the window and node.
                if reserved_ts:
                    return window, node
        # As a last resort, consider black-box nodes without TDP information.
        if len(blackbox) > 0:
            for start_hour in range(0, len(timeslots) - hours + 1):
                window = timeslots[start_hour : start_hour + hours]
                # Skip window if there is a full slot in it
                full_slots = list(filter(lambda x: x.is_full(), window))
                if len(full_slots) > 0:
                    continue
                for node in blackbox:
                    reserved_ts = _reserve_resources(
                        job_id=job_id, window=window, node=node
                    )
                    if reserved_ts:
                        return window, node
        # When reaching this point, allocation was unsuccessful
        return None, None


class SpatialShifting(PlanningStrategy):
    def allocate_resources(
        self,
        job_id: str,
        hours: int,
        timetable: Timetable,
        nodes: list[str],
        uses_gpu: bool,
    ) -> tuple[list[ConstrainedTimeslot], str]:
        """Allocate nodes considering their TDP values."""

        # Extract the available timeslots from the timetable.
        timeslots = timetable.timeslots

        # Initialize dictionaries and lists to categorize nodes:
        # 'tdp_box' will store nodes with their corresponding TDP values.
        # 'blackbox' will store nodes without TDP information.
        tdp_box = {}
        blackbox = []
        for node in nodes:
            if uses_gpu:
                tdp = get_gpu_tdp(hostname=node)
            else:
                tdp = get_cpu_tdp(hostname=node)
            if tdp is not None:
                tdp_box.update({node: tdp})
            else:
                blackbox.append(node)
        # Sort nodes in 'cpu_tdp_box' by their TDP values in ascending order.
        sorted_nodes = sorted(tdp_box.items(), key=lambda x: x[1])
        # Initialize load balancer pools, which map starting hours to pools of nodes.
        load_balance_pools = {}
        curr_pool = []  # Temporary list to hold the current pool of nodes.
        hour_marker = 0  # Tracks the starting hour for the current pool.

        # Create pools of nodes based on the difference in their TDP values.
        for i in range(len(sorted_nodes)):
            # Add the current node to the pool.
            node, tdp = sorted_nodes[i]
            curr_pool.append(node)
            # Calculate the TDP difference to the next node.
            if i < len(sorted_nodes) - 1:
                distance_next_tdp = sorted_nodes[i + 1][1] - tdp
            # If the TDP difference is non-zero, create a new pool.
            if distance_next_tdp != 0:
                # Calculate the next hour marker based on the TDP difference.
                next_marker = hour_marker + int(distance_next_tdp / 10)
                # Adjust the hour marker if it exceeds the available timeslots.
                if not hour_marker <= len(timeslots) - hours:
                    # Ensure marker is within bounds.
                    hour_marker = len(timeslots) - hours
                    # Merge the current pool with any existing pool at the last marker.
                    if hour_marker in load_balance_pools.keys():
                        prev_pool = load_balance_pools.get(len(timeslots) - hours)
                        prev_pool += curr_pool
                    else:
                        load_balance_pools.update({hour_marker: curr_pool})
                else:
                    # Otherwise, add the current pool to the load balance pools.
                    load_balance_pools.update({hour_marker: curr_pool})
                # Move the hour marker forward and reset the current pool.
                hour_marker = next_marker
                curr_pool = []

        # Initialize the list of allocation pools to try and allocate resources from.
        alloc_pools = []
        markers = list(load_balance_pools.keys())

        # Iterate over the hour markers to allocate resources.
        for i, marker in enumerate(markers):
            # Determine the range of timeslots for the current pool.
            if i < len(markers) - 1:
                next_marker = markers[i + 1]
            else:
                next_marker = len(timeslots) - 1
            # Add the current pool to the list of allocation pools.
            alloc_pools.append(load_balance_pools.get(marker))
            # Iterate through the available timeslots to find a valid window.
            for start_hour in range(next_marker - 1):
                window = timeslots[start_hour : start_hour + hours]
                # Skip window if there is a full slot in it
                full_slots = list(filter(lambda x: x.is_full(), window))
                if len(full_slots) > 0:
                    continue
                # Try to reserve resources using the pools in order.
                for pool in alloc_pools:
                    for node in pool:
                        reserved_ts = _reserve_resources(
                            job_id=job_id, window=window, node=node
                        )
                        # If resources are successfully reserved, return the window and node.
                        if reserved_ts:
                            return window, node
        # As a last resort, consider black-box nodes without TDP information.
        if len(blackbox) > 0:
            for start_hour in range(0, len(timeslots) - hours + 1):
                window = timeslots[start_hour : start_hour + hours]
                # Skip window if there is a full slot in it
                full_slots = list(filter(lambda x: x.is_full(), window))
                if len(full_slots) > 0:
                    continue
                for node in blackbox:
                    reserved_ts = _reserve_resources(
                        job_id=job_id, window=window, node=node
                    )
                    if reserved_ts:
                        return window, node
        # When reaching this point, allocation was unsuccessful
        return None, None


class SpatiotemporalShifting(PlanningStrategy):
    def allocate_resources(
        self,
        job_id: str,
        hours: int,
        timetable: Timetable,
        nodes: list[str],
        uses_gpu: bool,
    ) -> tuple[list[ConstrainedTimeslot], str]:
        """Allocate node considering its TDP values and the grid carbon intensity."""
        timeslots = timetable.timeslots
        # Spatial shifting preparation
        # 'cpu_tdp_box' will store nodes with their corresponding TDP values.
        # 'blackbox' will store nodes without TDP information.
        cpu_tdp_box = {}
        blackbox = []
        for node in nodes:
            cpu_tdp = get_cpu_tdp(hostname=node)
            if cpu_tdp is not None:
                cpu_tdp_box.update({node: cpu_tdp})
            else:
                blackbox.append(node)
        # Sort nodes in 'cpu_tdp_box' by their TDP values in ascending order.
        cpu_tdp_sorted_nodes = list(
            map(lambda x: x[0], sorted(cpu_tdp_box.items(), key=lambda x: x[1]))
        )

        # Construct list of windows. They are weighted regarding their forecasted carbon impact.
        fc_hours = len(timeslots)
        weighted_windows = {}
        for start_hour in range(0, fc_hours - hours + 1):
            # Map-reduce to calculate weight of current window
            window = timeslots[start_hour : start_hour + hours]
            # Skip window if there is a full slot in it
            full_slots = list(filter(lambda x: x.is_full(), window))
            if len(full_slots) > 0:
                continue
            # Calculate weight of window
            window_gcis = list(map(lambda x: x.gci, window))
            weight = reduce(lambda x, y: x + y, window_gcis)
            weighted_windows.update({weight: window})

            # Greedily allocate window with low carbon intensity
        for _, window in dict(sorted(weighted_windows.items())).items():
            reserved_ts = []
            # Reserve node (sorted after ascending TDP)
            for node in cpu_tdp_sorted_nodes:
                reserved_ts = _reserve_resources(
                    job_id=job_id, window=window, node=node
                )
                if reserved_ts:
                    return window, node
            # Consider node with unknown TDP
            for node in blackbox:
                reserved_ts = _reserve_resources(
                    job_id=job_id, window=window, node=node
                )
                if reserved_ts:
                    return window, node
        return None, None


def _reserve_resources(
    job_id: str, window: list[ConstrainedTimeslot], node: str
) -> list[str] | None:
    """Try to reserve node for a whole window.

    Allocates the whole timespan of the slots.
    """
    reserved_ts = []
    for timeslot in window:
        # If window contains a full timeslot, abort attempt.
        if timeslot.is_full():
            for ts in reserved_ts:
                ts.remove_job(job_id)
            reserved_ts.clear()
            return None
        # TODO: Allow partial start and end times to support other runtimes than full hours.
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
