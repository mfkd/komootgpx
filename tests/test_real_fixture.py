import json
import unittest
from pathlib import Path

from komootgpx.gpx import tour_to_gpx
from komootgpx.komoot import extract_payload_from_html, parse_tour_payload

FIXTURE = Path(__file__).parent / "fixtures" / "komoot_public_smarttour_33303609.payload.json"


def boot_html(payload: dict) -> str:
    encoded_payload = json.dumps(json.dumps(payload))
    return f"<script>kmtBoot.setProps({encoded_payload});</script>"


class RealFixtureTests(unittest.TestCase):
    def test_converts_captured_public_komoot_payload(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

        tour = parse_tour_payload(payload)
        gpx = tour_to_gpx(tour)

        self.assertEqual(
            tour.name,
            "Havelufer Forest Cycle Path \u2013 Tegeler Lake loop from Olympia-Stadion",
        )
        self.assertEqual(len(tour.coordinates), 2044)
        self.assertEqual(tour.coordinates[0].lat, 52.516839)
        self.assertEqual(tour.coordinates[0].lng, 13.25041)
        self.assertEqual(tour.coordinates[-1].lat, 52.516839)
        self.assertEqual(tour.coordinates[-1].lng, 13.25041)
        self.assertEqual(len(gpx.tracks[0].segments[0].points), 2044)

    def test_extracts_large_captured_payload_from_boot_script(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

        extracted = extract_payload_from_html(boot_html(payload))
        tour = parse_tour_payload(extracted)

        self.assertEqual(len(tour.coordinates), 2044)
        self.assertEqual(tour.coordinates[0].alt, 50.4)
