import json
import unittest
from unittest.mock import Mock, patch

import requests

from komootgpx.errors import KomootGpxError
from komootgpx.komoot import extract_payload_from_html, fetch_tour_html, parse_tour_payload


def boot_html(payload: dict) -> str:
    encoded_payload = json.dumps(json.dumps(payload))
    return f"<html><script>kmtBoot.setProps({encoded_payload});</script></html>"


def payload_with_coordinates(coordinates: list[dict]) -> dict:
    return {
        "page": {
            "_embedded": {
                "tour": {
                    "name": 'Morning "Road"); Ride',
                    "_embedded": {"coordinates": {"items": coordinates}},
                }
            }
        }
    }


class ExtractPayloadTests(unittest.TestCase):
    def test_extracts_boot_payload(self) -> None:
        payload = payload_with_coordinates([{"lat": 51.5, "lng": -0.12, "alt": 35}])

        extracted = extract_payload_from_html(boot_html(payload))

        self.assertEqual(extracted, payload)

    def test_missing_boot_marker_fails_clearly(self) -> None:
        with self.assertRaisesRegex(KomootGpxError, "Could not find Komoot tour data"):
            extract_payload_from_html("<html></html>")

    def test_malformed_json_fails_clearly(self) -> None:
        html = '<script>kmtBoot.setProps("{bad json");</script>'

        with self.assertRaisesRegex(KomootGpxError, "Could not parse Komoot tour data"):
            extract_payload_from_html(html)


class FetchTourHtmlTests(unittest.TestCase):
    def test_fetches_with_user_agent_and_timeout(self) -> None:
        response = Mock(status_code=200, text="<html></html>")
        response.raise_for_status.return_value = None

        with patch("komootgpx.komoot.requests.get", return_value=response) as get:
            html = fetch_tour_html("https://www.komoot.com/tour/1", timeout=3)

        self.assertEqual(html, "<html></html>")
        get.assert_called_once_with(
            "https://www.komoot.com/tour/1",
            headers={"User-Agent": "komootgpx/0.1"},
            timeout=3,
        )

    def test_fetch_reports_private_or_blocked_tour(self) -> None:
        response = Mock(status_code=403)

        with patch("komootgpx.komoot.requests.get", return_value=response):
            with self.assertRaisesRegex(KomootGpxError, "HTTP 403"):
                fetch_tour_html("https://www.komoot.com/tour/1")

    def test_fetch_wraps_network_errors(self) -> None:
        with patch(
            "komootgpx.komoot.requests.get",
            side_effect=requests.ConnectionError("offline"),
        ):
            with self.assertRaisesRegex(KomootGpxError, "Failed to download"):
                fetch_tour_html("https://www.komoot.com/tour/1")


class ParseTourPayloadTests(unittest.TestCase):
    def test_parses_tour_with_missing_altitude(self) -> None:
        payload = payload_with_coordinates([{"lat": 51.5, "lng": -0.12}])

        tour = parse_tour_payload(payload)

        self.assertEqual(tour.name, 'Morning "Road"); Ride')
        self.assertEqual(tour.coordinates[0].lat, 51.5)
        self.assertEqual(tour.coordinates[0].lng, -0.12)
        self.assertIsNone(tour.coordinates[0].alt)

    def test_rejects_empty_coordinates(self) -> None:
        with self.assertRaisesRegex(KomootGpxError, "no coordinates"):
            parse_tour_payload(payload_with_coordinates([]))

    def test_rejects_missing_tour_name(self) -> None:
        payload = payload_with_coordinates([{"lat": 51.5, "lng": -0.12}])
        payload["page"]["_embedded"]["tour"]["name"] = ""

        with self.assertRaisesRegex(KomootGpxError, "missing a tour name"):
            parse_tour_payload(payload)

    def test_rejects_missing_coordinate_fields(self) -> None:
        with self.assertRaisesRegex(KomootGpxError, "missing lng"):
            parse_tour_payload(payload_with_coordinates([{"lat": 51.5}]))

    def test_rejects_invalid_latitude(self) -> None:
        with self.assertRaisesRegex(KomootGpxError, "invalid latitude"):
            parse_tour_payload(payload_with_coordinates([{"lat": 91, "lng": -0.12}]))

    def test_rejects_non_numeric_longitude(self) -> None:
        with self.assertRaisesRegex(KomootGpxError, "non-numeric lng"):
            parse_tour_payload(payload_with_coordinates([{"lat": 51.5, "lng": "west"}]))
