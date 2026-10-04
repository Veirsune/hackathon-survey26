"""Exposure threshold cache distinguishes scenario physics and time bounds."""
import unittest
from agent_core.optimizer import duration_to_factor


class ThresholdCacheTests(unittest.TestCase):
    def test_shared_cache_keeps_different_throughput_scenarios_separate(self):
        item = dict(factor_scale=.001, quality_coefficients=(1., 0., 0.), _exposure_cache={})
        self.assertEqual(duration_to_factor(item, 1., 60, 2000), 1000)
        self.assertEqual(duration_to_factor(dict(item, factor_scale=.002), 1., 60, 2000), 500)
        self.assertEqual(duration_to_factor(dict(item, quality_coefficients=(.5, 0., 0.)), 1., 60, 3000), 2000)
        self.assertEqual(duration_to_factor(item, 1., 60, 2000), 1000)

    def test_threshold_and_bounds_isolate_unreachable_results(self):
        item = dict(factor_scale=.001, quality_coefficients=(1., 0., 0.), _exposure_cache={})
        self.assertIsNone(duration_to_factor(item, 1., 60, 999))
        self.assertEqual(duration_to_factor(item, 1., 60, 1000), 1000)
        self.assertEqual(duration_to_factor(item, .5, 60, 999), 500)
        self.assertEqual(duration_to_factor(item, .5, 700, 999), 700)
        self.assertIsNone(duration_to_factor(item, .5, 1000, 999))
