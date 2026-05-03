import unittest

from komootgpx.gpx import tour_to_gpx
from komootgpx.komoot import Coordinate, Tour


class GpxConversionTests(unittest.TestCase):
    def test_converts_tour_to_single_track_gpx(self) -> None:
        tour = Tour(
            name="Test route",
            coordinates=[
                Coordinate(lat=51.5, lng=-0.12, alt=35),
                Coordinate(lat=51.6, lng=-0.13),
            ],
        )

        gpx = tour_to_gpx(tour)
        xml = gpx.to_xml()

        self.assertEqual(gpx.name, "Test route")
        self.assertEqual(len(gpx.tracks), 1)
        self.assertEqual(len(gpx.tracks[0].segments), 1)
        self.assertEqual(len(gpx.tracks[0].segments[0].points), 2)
        self.assertIn("<gpx", xml)
        self.assertIn("<name>Test route</name>", xml)
