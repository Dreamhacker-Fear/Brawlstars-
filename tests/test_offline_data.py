import unittest

from offline_data import load_maps, load_projectiles, load_scenarios, plan_dodge


class OfflineDataTests(unittest.TestCase):
    def test_maps_load_and_have_dimensions(self):
        maps = load_maps()
        self.assertIn("open_training", maps)
        self.assertGreater(maps["open_training"]["width"], 0)

    def test_projectile_presets_load(self):
        projectiles = load_projectiles()
        self.assertIn("straight", projectiles)
        self.assertGreater(projectiles["straight"]["speed"], 0)

    def test_scenarios_have_valid_maps(self):
        maps = load_maps()
        scenarios = load_scenarios()
        self.assertGreaterEqual(len(scenarios), 3)
        for scenario in scenarios:
            self.assertIn(scenario["map"], maps)

    def test_planner_returns_finite_direction(self):
        maps = load_maps()
        for scenario in load_scenarios():
            result = plan_dodge(scenario, maps[scenario["map"]])
            dx, dy = result["direction"]
            self.assertTrue(-1.000001 <= dx <= 1.000001)
            self.assertTrue(-1.000001 <= dy <= 1.000001)
            self.assertTrue(result["cost"] >= 0)


if __name__ == "__main__":
    unittest.main()
