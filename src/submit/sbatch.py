"""Submit sbatch jobs"""

from datetime import datetime, UTC
from uuid import uuid4

from src.cluster.commons import sbatch
from src.sched.scheduler import schedule_job


def submit_sbatch(command: str, runtime: int):
    """Submit a Slurm job in a carbon-aware manner."""
    now = datetime.now(tz=UTC)
    # TODO: Get partitions from arguments
    start_timeslot = schedule_job(
        job_id=str(uuid4()), runtime=runtime, submit_date=now, partitions=["admin"]
    )
    delta = (start_timeslot - now).seconds
    print(
        sbatch(suffix=f"{command.strip()} --time={runtime}:00:00 --begin=now+{delta}")
    )


def simulate_submit_sbatch(command: str, runtime: int, submit_date: str):
    """Simulate submitting a Slurm job in a carbon-aware manner."""
    # TODO: Get partitions from arguments
    submit_date = (
        datetime.fromisoformat(submit_date)
        if submit_date is not None
        else datetime.now(tz=UTC)
    )
    start_timeslot = schedule_job(
        job_id=str(uuid4()),
        runtime=runtime,
        submit_date=submit_date,
        partitions=["admin"],
    )
    delta = (start_timeslot - submit_date).seconds
    print(f"sbatch {command.strip()} --time={runtime}:00:00 --begin=now+{delta}")
