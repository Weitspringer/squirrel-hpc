"""Submit sbatch jobs"""

from datetime import datetime, UTC
from uuid import uuid4

from src.cluster.commons import sbatch
from src.config.squirrel_conf import Config
from src.data.timetable import tt_from_csv, tt_to_csv
from src.sched.scheduler import Scheduler, SpatiotemporalShifting


def submit_sbatch(
    command: str, runtime: int, partitions: list[str], num_gpus: int, gpu_name: str
):
    """Submit a Slurm job in a carbon-aware manner."""
    scheduler = Scheduler(
        strategy=SpatiotemporalShifting(),
        cluster_info=Config.get_local_paths()["cluster_json"],
    )
    now = datetime.now(tz=UTC)
    timetable = tt_from_csv(start=now)
    start_timeslot, node = scheduler.schedule_sbatch(
        timetable=timetable,
        job_id=str(uuid4()),
        hours=runtime,
        partitions=partitions,
        num_gpus=num_gpus,
        gpu_name=gpu_name,
    )
    delta = (start_timeslot - now).seconds
    print(
        f"Schedule job on node {node} in {delta} seconds.",
        sbatch(
            suffix=f"{command.strip()} --time={runtime}:00:00 --begin=now+{delta} --nodelist={node} --exclusive"
        ),
    )
    tt_to_csv(timetable)


def simulate_submit_sbatch(
    command: str,
    runtime: int,
    submit_date: datetime,
    partitions: list[str],
    num_gpus: int,
    gpu_name: str,
):
    """Simulate submitting a Slurm job in a carbon-aware manner."""
    scheduler = Scheduler(
        strategy=SpatiotemporalShifting(),
        cluster_info=Config.get_local_paths()["cluster_json"],
    )
    timetable = tt_from_csv(start=submit_date)
    start_timeslot, node = scheduler.schedule_sbatch(
        timetable=timetable,
        job_id=str(uuid4()),
        hours=runtime,
        partitions=partitions,
        num_gpus=num_gpus,
        gpu_name=gpu_name,
    )
    delta = (start_timeslot - submit_date).seconds
    print(f"Schedule job on node {node} in {delta} seconds.")
    tt_to_csv(timetable)
