import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from komootgpx.cli import main


def boot_html() -> str:
    payload = {
        "page": {
            "_embedded": {
                "tour": {
                    "name": "Test route",
                    "_embedded": {
                        "coordinates": {
                            "items": [
                                {"lat": 51.5, "lng": -0.12, "alt": 35},
                                {"lat": 51.6, "lng": -0.13},
                            ]
                        }
                    },
                }
            }
        }
    }
    return f"<script>kmtBoot.setProps({json.dumps(json.dumps(payload))});</script>"


class CliTests(unittest.TestCase):
    def test_main_writes_gpx_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "route.gpx"

            with patch("komootgpx.cli.fetch_tour_html", return_value=boot_html()):
                exit_code = main(["https://www.komoot.com/tour/1", "-o", str(output)])

            self.assertEqual(exit_code, 0)
            self.assertIn("<gpx", output.read_text(encoding="utf-8"))

    def test_main_prints_concise_error_by_default(self) -> None:
        stderr = io.StringIO()

        with patch("komootgpx.cli.fetch_tour_html", return_value="<html></html>"):
            with redirect_stderr(stderr):
                exit_code = main(["https://www.komoot.com/tour/1", "-o", "route.gpx"])

        self.assertEqual(exit_code, 1)
        self.assertIn("error:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_main_prints_traceback_when_verbose(self) -> None:
        stderr = io.StringIO()

        with patch("komootgpx.cli.fetch_tour_html", return_value="<html></html>"):
            with redirect_stderr(stderr):
                exit_code = main(
                    ["https://www.komoot.com/tour/1", "-o", "route.gpx", "--verbose"]
                )

        self.assertEqual(exit_code, 1)
        self.assertIn("Traceback", stderr.getvalue())

    def test_main_reports_output_write_failures(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("komootgpx.cli.fetch_tour_html", return_value=boot_html()):
                with redirect_stderr(stderr):
                    exit_code = main(["https://www.komoot.com/tour/1", "-o", temp_dir])

        self.assertEqual(exit_code, 1)
        self.assertIn("Could not write GPX file", stderr.getvalue())
