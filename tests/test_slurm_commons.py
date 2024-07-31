"""Slurm commons"""

from pathlib import Path
import unittest

from src.cluster import commons as mut  # module-under-test


class TestSlurmCommons(unittest.TestCase):
    """Test Slurm utility methods."""

    def test_read_sinfo(self):
        """Tests if output of `sinfo --json` is parsed correctly."""
        sinfo_dict = mut.read_sinfo(Path("tests") / "data" / "sinfo.json")
        assert len(sinfo_dict.keys()) == 3
        assert all(k in sinfo_dict.keys() for k in ["meta", "errors", "nodes"])


if __name__ == "__main__":
    unittest.main()
