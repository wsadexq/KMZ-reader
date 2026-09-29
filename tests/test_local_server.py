from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parents[1]))

from local_server import start_server
from route_model import RouteModel, Waypoint


class LocalServerTests(unittest.TestCase):
    def test_route_requires_token(self):
        server, thread, url = start_server(RouteModel("route.kmz", waypoints=[Waypoint(0, 120, 30)]))
        try:
            token = server.preview_token
            api_url = url.split("/#", 1)[0] + "/api/route"
            with self.assertRaises(HTTPError):
                urlopen(api_url, timeout=3)
            with urlopen(Request(api_url, headers={"X-Preview-Token": token}), timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Referrer-Policy"], "strict-origin-when-cross-origin")
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                self.assertIn("https://tile.openstreetmap.org", response.headers["Content-Security-Policy"])
                self.assertIn(b"route.kmz", response.read())
            with urlopen(url, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"KMZ", response.read())
            cesium_url = url.split("/#", 1)[0] + "/vendor/cesium/Cesium.js"
            with urlopen(cesium_url, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Content-Type"], "text/javascript; charset=utf-8")
        finally:
            server.shutdown()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
