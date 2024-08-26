"""Configuration for Squirrel."""

from pathlib import Path

from src.config.ini_conf import IniConfig


class ClusterInfo(IniConfig):
    """Reads additional information about cluster nodes."""

    def get_cpu_tdp(self, node: str) -> int | None:
        """Get TDP of a node's CPU."""
        if not self._check_node_section(node=node) or not self.conf.has_option(
            section=f"nodes.{node}.cpus", option="tdp"
        ):
            return None
        try:
            return int(self.conf.get(f"nodes.{node}.cpus", "tdp"))
        except ValueError:
            return None

    def get_gpu_tdp(self, node: str) -> int | None:
        """Get TDP of a node's GPU."""
        if not self._check_node_section(node=node) or not self.conf.has_option(
            section=f"nodes.{node}.gpus", option="tdp"
        ):
            return None
        try:
            return int(self.conf.get(f"nodes.{node}.gpus", "tdp"))
        except ValueError:
            return None

    def _check_node_section(self, node: str) -> None:
        return self.conf.has_section(f"nodes.{node}")


Config = ClusterInfo(
    path=Path(__file__).resolve().parent / ".." / ".." / "config" / "cluster_info.cfg"
)
