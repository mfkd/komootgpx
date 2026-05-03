import os
import unittest

from komootgpx.gpx import tour_to_gpx
from komootgpx.komoot import extract_payload_from_html, fetch_tour_html, parse_tour_payload

LIVE_URL = os.environ.get("KOMOOTGPX_LIVE_URL")


@unittest.skipUnless(LIVE_URL, "set KOMOOTGPX_LIVE_URL to run live Komoot integration test")
class LiveKomootTests(unittest.TestCase):
    def test_live_public_tour_converts_to_gpx(self) -> None:
        assert LIVE_URL is not None

        html = fetch_tour_html(LIVE_URL)
        payload = extract_payload_from_html(html)
        tour = parse_tour_payload(payload)
        gpx = tour_to_gpx(tour)

        self.assertTrue(tour.name.strip())
        self.assertGreater(len(tour.coordinates), 0)
        self.assertEqual(len(gpx.tracks), 1)
        self.assertEqual(len(gpx.tracks[0].segments), 1)
        self.assertEqual(len(gpx.tracks[0].segments[0].points), len(tour.coordinates))
