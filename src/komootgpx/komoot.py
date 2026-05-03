from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from html import unescape
from typing import Any

import requests

from .errors import KomootGpxError

BOOT_MARKER = 'kmtBoot.setProps("'
USER_AGENT = "komootgpx/0.1"


@dataclass(frozen=True)
class Coordinate:
    lat: float
    lng: float
    alt: float | None = None


@dataclass(frozen=True)
class Tour:
    name: str
    coordinates: list[Coordinate]


def fetch_tour_html(url: str, timeout: float = 10.0) -> str:
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise KomootGpxError(f"Failed to download Komoot page: {exc}") from exc

    if response.status_code == 403:
        raise KomootGpxError(
            "Komoot returned HTTP 403. The tour may be private or automated access may be blocked."
        )
    if response.status_code == 404:
        raise KomootGpxError("Komoot returned HTTP 404. Check that the tour URL is correct.")

    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        raise KomootGpxError(f"Komoot returned an HTTP error: {exc}") from exc

    return response.text


def extract_payload_from_html(html: str) -> dict[str, Any]:
    source = html if BOOT_MARKER in html else unescape(html)
    start = source.find(BOOT_MARKER)
    if start == -1:
        raise KomootGpxError(
            "Could not find Komoot tour data in the page. Komoot may have changed its page format."
        )

    raw_js_string = _read_boot_string(source, start + len(BOOT_MARKER))
    decoded_json = _decode_js_string(raw_js_string)

    for candidate in (decoded_json, unescape(decoded_json)):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
        raise KomootGpxError("Komoot tour data was not a JSON object.")

    raise KomootGpxError(
        "Could not parse Komoot tour data. Komoot may have changed its page format."
    )


def parse_tour_payload(payload: Mapping[str, Any]) -> Tour:
    try:
        tour = payload["page"]["_embedded"]["tour"]
        coordinate_items = tour["_embedded"]["coordinates"]["items"]
    except (KeyError, TypeError) as exc:
        raise KomootGpxError(
            "Komoot tour data is missing the expected tour coordinates."
        ) from exc

    if not isinstance(tour, Mapping):
        raise KomootGpxError("Komoot tour data is not in the expected format.")

    name = tour.get("name")
    if not isinstance(name, str) or not name.strip():
        raise KomootGpxError("Komoot tour data is missing a tour name.")

    if not isinstance(coordinate_items, list):
        raise KomootGpxError("Komoot tour coordinates are not in the expected format.")
    if not coordinate_items:
        raise KomootGpxError("Komoot tour has no coordinates.")

    coordinates = [
        _parse_coordinate(item, index) for index, item in enumerate(coordinate_items, start=1)
    ]
    return Tour(name=name, coordinates=coordinates)


def _read_boot_string(source: str, start: int) -> str:
    escaped = False

    for index in range(start, len(source)):
        char = source[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            end = index + 1
            while end < len(source) and source[end].isspace():
                end += 1
            if source.startswith(");", end):
                return source[start:index]
            raise KomootGpxError(
                "Could not read Komoot tour data. Komoot may have changed its page format."
            )

    raise KomootGpxError("Could not find the end of Komoot tour data in the page.")


def _decode_js_string(raw_value: str) -> str:
    try:
        decoded = json.loads(f'"{raw_value}"')
    except json.JSONDecodeError as exc:
        raise KomootGpxError(
            "Could not decode Komoot tour data. Komoot may have changed its page format."
        ) from exc

    if not isinstance(decoded, str):
        raise KomootGpxError("Komoot tour data was not encoded as text.")
    return decoded


def _parse_coordinate(item: Any, index: int) -> Coordinate:
    if not isinstance(item, Mapping):
        raise KomootGpxError(f"Coordinate {index} is not in the expected format.")

    lat = _required_number(item, "lat", index)
    lng = _required_number(item, "lng", index)
    alt = _optional_number(item.get("alt"), "alt", index)

    if not -90 <= lat <= 90:
        raise KomootGpxError(f"Coordinate {index} has invalid latitude {lat}.")
    if not -180 <= lng <= 180:
        raise KomootGpxError(f"Coordinate {index} has invalid longitude {lng}.")

    return Coordinate(lat=lat, lng=lng, alt=alt)


def _required_number(item: Mapping[str, Any], field: str, index: int) -> float:
    if field not in item:
        raise KomootGpxError(f"Coordinate {index} is missing {field}.")
    return _number(item[field], field, index)


def _optional_number(value: Any, field: str, index: int) -> float | None:
    if value is None:
        return None
    return _number(value, field, index)


def _number(value: Any, field: str, index: int) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise KomootGpxError(f"Coordinate {index} has non-numeric {field}.")
    return float(value)
