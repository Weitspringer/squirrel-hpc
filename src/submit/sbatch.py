"""Submit sbatch jobs"""

from datetime import datetime, UTC
from uuid import uuid4

from src.cluster.commons import sbatch
from src.sched.scheduler import schedule_job


def submit_sbatch(command: str, runtime: int):
    """Submit a Slurm job with time shifting."""
    now = datetime.now(tz=UTC)
    start_timeslot = schedule_job(job_id=str(uuid4()), runtime=runtime, submit_date=now)
    delta = (start_timeslot - now).seconds
    print(f"{command.strip()} --time={runtime}:00:00 --begin={delta}")
    print(sbatch(suffix=f"{command.strip()} --time={runtime}:00:00 --begin={delta}"))
