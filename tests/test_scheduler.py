"""Squirrel scheduler"""

from pathlib import Path
import unittest

from src.sched import scheduler as mut  # module-under-test


class TestSlurmCommons(unittest.TestCase):
    """Test scheduler methods."""

    def test_get_nodes(self):
        """Test retrieving nodes based on partitions and 1 GPU."""

        # Instantiate the class and call _get_nodes
        obj = mut.Scheduler(
            strategy=mut.CarbonAgnosticFifo(),
            cluster_info=Path("src") / "sim" / "data" / "multi-node-cluster.json",
        )
        result = obj._get_nodes(partitions=["simsala"], num_gpus=1)

        # Expected result after sorting by weight and name
        expected_result = ["g01"]

        # Check if the result matches the expected nodes
        self.assertEqual(result, expected_result)

    def test_get_nodes_insufficient_resources(self):
        """Test _get_nodes when requesting too many resources for the cluster."""

        # Instantiate the class and call _get_nodes
        obj = mut.Scheduler(
            strategy=mut.CarbonAgnosticFifo(),
            cluster_info=Path("src") / "sim" / "data" / "multi-node-cluster.json",
        )
        result = obj._get_nodes(partitions=["simsala"], num_gpus=3)

        # Expected result after sorting by weight and name
        expected_result = []

        # Check if the result matches the expected nodes
        self.assertEqual(result, expected_result)

    def test_get_nodes_no_gpus(self):
        """Test _get_nodes with no GPU filter."""

        # Instantiate the class and call _get_nodes
        obj = mut.Scheduler(
            strategy=mut.CarbonAgnosticFifo(),
            cluster_info=Path("src") / "sim" / "data" / "multi-node-cluster.json",
        )
        result = obj._get_nodes(partitions=["kadabra"])

        # Expected result after sorting by weight and name
        expected_result = ["c01", "c02", "c03", "g01"]

        # Check if the result matches the expected nodes
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
