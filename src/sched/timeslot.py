"""Timeslot"""

from datetime import datetime
from uuid import uuid4


class ConstrainedTimeslot:
    """Timeslot with constraints."""

    def __init__(
        self,
        start: datetime,
        end: datetime,
        gci: float,
        jobs: dict,
        reserved_resources: dict[str, dict],
    ) -> None:
        """Timeslot with constraints."""
        self.start = start
        self.end = end
        self.gci = gci
        self.jobs = jobs
        self.reserved_resources = reserved_resources
        self.full_flag = False

    def get_duration(self):
        """Returns the duration of the time slot in seconds."""
        return (self.end - self.start).total_seconds()

    def get_gci(self):
        """Get the grid carbon intensity for this time slot."""
        return self.gci

    def set_gci(self, gci: int):
        """Set the grid carbon intensity for this time slot."""
        self.gci = gci

    def flag_full(self):
        """Mark the timeslot as full to save time."""
        self.full_flag = True

    def is_full(self) -> bool:
        """Determine wether this timeslot is available or not."""
        return self.full_flag

    def allocate_node_exclusive(
        self, job_id: str, node_name: str, start: datetime, end: datetime
    ) -> str:
        """Request node for a specified duration."""
        if not (start >= self.start and end <= self.end):
            return None
        # Check if there is a conflicting reservation
        for _, r_batch in self.reserved_resources.items():
            # Check node name
            if r_batch.get("node") != node_name:
                continue
            # Check if requested times overlap
            r_start = datetime.fromisoformat(r_batch.get("start"))
            r_end = datetime.fromisoformat(r_batch.get("end"))
            if (end >= r_start and end <= r_end) or (
                start >= r_start and start <= r_end
            ):
                return None
        # Request successful
        request_uuid = str(uuid4())
        reservation = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "node": node_name,
        }
        self.reserved_resources.update({request_uuid: reservation})
        self.jobs.update({job_id: request_uuid})
        return request_uuid

    def remove_job(self, job_id: str) -> None:
        """Frees allocated resources."""
        res_id = self.jobs.pop(job_id)
        self.reserved_resources.pop(res_id)

    def __eq__(self, value: object) -> bool:
        """Defines when 2 time slots are equal."""
        if not isinstance(value, ConstrainedTimeslot):
            return False
        return self.start == value.start and self.end == value.end
