"""Slurm commons"""

from pathlib import Path
import unittest

from src.cluster import commons as mut  # module-under-test


class TestSlurmCommons(unittest.TestCase):
    """Test Slurm utility methods."""

    def test_sinfo(self):
        """Tests if output of `sinfo --json` is parsed correctly."""
        path_to_json = Path("src") / "sim" / "data" / "3-node-cluster.json"
        sinfo_dict = mut.read_sinfo(path_to_json=path_to_json)
        assert len(sinfo_dict.keys()) == 4
        assert all(
            k in sinfo_dict.keys() for k in ["meta", "errors", "warnings", "nodes"]
        )
        nodes = mut.get_nodes(path_to_json=path_to_json)
        assert len(nodes) == 3
        partitions = mut.get_partitions(path_to_json=path_to_json)
        assert len(partitions.keys()) == 3


if __name__ == "__main__":
    unittest.main()
