"""Carbon Conversion"""

import unittest

from research.carbon_emmissions import conversion as mut  # module-under-test


class TestCarbonConversionMethods(unittest.TestCase):
    """Test carbon conversion methods"""

    def test_carbon_estimation_constant(self):
        """Emmissions from constant power and carbon intensity."""
        power_w = [1000, 1000]
        carbon = [300, 300]
        unix_seconds = [1716903000, 1716906600]  # 1 hour
        emmissions = mut.estimate_carbon_emmissions(
            power_w=power_w, gco2_per_kwh=carbon, unix_seconds=unix_seconds
        )
        assert emmissions == 300


if __name__ == "__main__":
    unittest.main()
