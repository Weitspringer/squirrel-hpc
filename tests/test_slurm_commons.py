"""Slurm commons"""

from pathlib import Path
import unittest

from src.cluster import commons as mut  # module-under-test


class TestSlurmCommons(unittest.TestCase):
    """Test Slurm utility methods."""

    def test_sinfo(self):
        """Tests if output of `sinfo --json` is parsed correctly."""
        path_to_json = Path("tests") / "data" / "sinfo.json"
        sinfo_dict = mut.read_sinfo(path_to_json=path_to_json)
        assert len(sinfo_dict.keys()) == 3
        assert all(k in sinfo_dict.keys() for k in ["meta", "errors", "nodes"])
        nodes = mut.get_nodes(path_to_json=path_to_json)
        assert nodes.shape[0] == 3
        partitions = mut.get_partitions(path_to_json=path_to_json)
        assert len(partitions.keys()) == 4


if __name__ == "__main__":
    unittest.main()
