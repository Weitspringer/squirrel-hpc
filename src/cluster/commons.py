"""Manage the Slurm cluster.

Many of these functions are adapted from GreenSlot (Goiri et al., 2015).
DOI: 10.1016/j.adhoc.2014.11.012
https://github.com/goiri/greenslot/blob/master/gslurmcommons.py
"""

from json import loads
from pathlib import Path
from subprocess import call, PIPE, check_output


def sbatch(suffix: str) -> str:
    """Execute sbatch with trailing suffix.

    Args:
        suffix (str): `sbatch <suffix>` will be executed.

    Returns:
        int: Returns answer from sbatch.
    """
    cmd = ["sbatch"] + suffix.split()
    out = check_output(cmd).decode()
    return out


def read_sinfo(path_to_json: Path | None = None) -> dict:
    """Parses the output of 'sinfo --json'."""
    if path_to_json is None:
        cmd = ["sinfo", "--json"]
        out = check_output(cmd).decode()
    else:
        out = path_to_json.read_text()
    return loads(out)


def set_job_priority(job_id: str, priority: str) -> int:
    """Change the priority of a job.

    Args:
        job_id (str): Job ID.
        priority (str): Priority

    Returns:
        int: Return code of scontrol.
    """
    return call(
        ["scontrol", "-o", "update", "JobId=" + job_id, "Priority=" + priority],
        stderr=PIPE,
    )


def suspend_job(job_id: str) -> int:
    """Suspend a job.

    Args:
        job_id (str): Job ID.

    Returns:
        int: Return code of scontrol.
    """
    return call(["scontrol", "suspend", job_id], stderr=PIPE)


def resume_job(job_id: str) -> int:
    """Resume a suspended job.

    Args:
        job_id (str): Job ID.

    Returns:
        int: Return code of scontrol.
    """
    return call(["scontrol", "resume", job_id], stderr=PIPE)


def cancel_job(job_id: str) -> int:
    """Cancel a job.

    Args:
        job_id (str): Job ID.

    Returns:
        int: Return code of scancel.
    """
    return call(["scancel", job_id], stderr=PIPE)
