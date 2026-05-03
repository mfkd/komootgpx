from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Sequence

from .errors import KomootGpxError
from .gpx import tour_to_gpx, write_gpx
from .komoot import extract_payload_from_html, fetch_tour_html, parse_tour_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a public Komoot tour URL to GPX")
    parser.add_argument("url", help="Public Komoot tour URL")
    parser.add_argument("-o", "--output", required=True, help="GPX file to create")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show tracebacks for debugging failures",
    )
    return parser


def convert_url_to_gpx(url: str, output: str) -> None:
    html = fetch_tour_html(url)
    payload = extract_payload_from_html(html)
    tour = parse_tour_payload(payload)
    gpx = tour_to_gpx(tour)
    write_gpx(gpx, output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        convert_url_to_gpx(args.url, args.output)
    except KomootGpxError as exc:
        _print_error(exc, verbose=args.verbose)
        return 1
    except OSError as exc:
        _print_error(f"Could not write GPX file: {exc}", verbose=args.verbose, exc=exc)
        return 1

    return 0


def _print_error(
    message: object,
    *,
    verbose: bool,
    exc: BaseException | None = None,
) -> None:
    print(f"error: {message}", file=sys.stderr)
    if verbose:
        error = exc if exc is not None else message
        if isinstance(error, BaseException):
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
