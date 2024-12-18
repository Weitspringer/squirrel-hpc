"""Manage the Slurm cluster.

Some of these functions are adapted from GreenSlot (Goiri et al., 2015).
DOI: 10.1016/j.adhoc.2014.11.012
https://github.com/goiri/greenslot/blob/master/gslurmcommons.py
"""

from json import loads
from pathlib import Path
from subprocess import call, PIPE, check_output
from typing import Any

from src.config.cluster_info import NodesMeta


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
    """Parses the output of 'scontrol show node --json'."""
    if path_to_json is None:
        cmd = ["scontrol", "show", "node", "--json"]
        out = check_output(cmd).decode()
    else:
        out = path_to_json.read_text()
    j_data = loads(out)
    if "nodes" not in j_data.keys():
        raise ValueError(
            "Unknown format of cluster configuration. Needs 'nodes' section."
        )
    return j_data


def get_nodes(path_to_json: Path | None = None) -> list[dict[str, Any]]:
    """Get all nodes of the cluster."""
    return read_sinfo(path_to_json=path_to_json).get("nodes")


def get_cpu_tdp(node_name: str, meta_info: NodesMeta) -> int | None:
    """Get thermal design power (TDP) of a node's CPUs.
    The node is defined by its name.

    If TDP was not provided, returns None.
    """
    return meta_info.get_cpu_tdp(node=node_name)


def get_gpu_tdp(node_name: str, meta_info: NodesMeta) -> int | None:
    """Get thermal design power (TDP) of a node's GPUs.
    The node is defined by its name.

    If TDP was not provided, returns None.
    """
    return meta_info.get_gpu_tdp(node=node_name)


def get_partitions(path_to_json: Path | None = None) -> dict[str, dict[str, Any]]:
    """Get nodes for every partition."""
    part_dict = {}
    nodes = get_nodes(path_to_json=path_to_json)
    for node in nodes:
        partitions = node["partitions"]
        for part_name in partitions:
            if part_name not in part_dict.keys():
                part_dict.update({part_name: []})
            part_dict[part_name].append(node)
    return part_dict


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
