"""Submit sbatch jobs"""

from uuid import uuid4

from src.sched.scheduler import schedule_job


def submit_sbatch(command: str, runtime: int):
    """Submit a Slurm job with time shifting."""

    start_timeslot = schedule_job(job_id=str(uuid4()), runtime=runtime)
    print(f"{command.strip()} --running {runtime}")
    print(start_timeslot)
