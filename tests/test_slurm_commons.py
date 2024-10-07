"""Slurm commons"""

from pathlib import Path
import unittest

from src.cluster import commons as mut  # module-under-test


class TestSlurmCommons(unittest.TestCase):
    """Test Slurm utility methods."""

    def test_sinfo(self):
        """Tests if output of `sinfo --json` is parsed correctly."""
        path_to_json = Path("src") / "sim" / "data" / "multi-node-cluster.json"
        sinfo_dict = mut.read_sinfo(path_to_json=path_to_json)
        assert len(sinfo_dict.keys()) == 3
        assert all(k in sinfo_dict.keys() for k in ["meta", "errors", "nodes"])
        nodes = mut.get_nodes(path_to_json=path_to_json)
        assert len(nodes) == 4
        partitions = mut.get_partitions(path_to_json=path_to_json)
        assert len(partitions.keys()) == 4

    def test_sort_nodes(self):
        """Test sorting of nodes by weight and name."""
        nodes = [
            {"name": "node2", "weight": 10},
            {"name": "node1", "weight": 10},
            {"name": "node3", "weight": 5},
            {"name": "node4", "weight": 15},
        ]

        expected_result = [
            {"name": "node3", "weight": 5},
            {"name": "node1", "weight": 10},
            {"name": "node2", "weight": 10},
            {"name": "node4", "weight": 15},
        ]

        result = mut._sort_nodes(nodes)

        # Check if the result matches the expected sorted order
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
