"""Submit sbatch jobs"""

from src.sched.scheduler import schedule_job


def submit_sbatch(command: str, runtime: int):
    """Submit a Slurm job with time shifting."""

    start_timeslot = schedule_job(runtime)
    print(start_timeslot)

    print(command, runtime)
