from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from route_model import RouteModel, Waypoint, haversine_meters


class RouteModelTests(unittest.TestCase):
    def test_haversine(self):
        self.assertAlmostEqual(haversine_meters(0, 0, 0, 1) / 1000, 111.195, delta=0.2)

    def test_statistics_and_serialization(self):
        model = RouteModel("route.kmz", waypoints=[Waypoint(0, 120, 30, height=20, speed=5), Waypoint(1, 120.001, 30.001, height=25, speed=6)])
        stats = model.compute_statistics()
        self.assertEqual(stats["waypointCount"], 2)
        self.assertEqual(stats["minHeight"], 20)
        self.assertIn("statistics", model.to_dict())


if __name__ == "__main__":
    unittest.main()
