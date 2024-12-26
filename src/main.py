"""
Command-line tool to convert Komoot tour URLs to GPX format.
Downloads tour data from Komoot and saves it as a GPX file for use in GPS devices
or other mapping applications.
"""

import argparse
import json
import sys
import traceback
from html import unescape
from typing import Any

import gpxpy
import gpxpy.gpx
import requests


def make_http_request(url: str) -> str:
    """
    Make an HTTP GET request and return the response content as a string.

    Args:
        url: The URL to request

    Returns:
        str: The response content

    Raises:
        requests.RequestException: If the HTTP request fails
    """
    headers = {"User-Agent": "komootgpx"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def sanitize_json_string(json_string: str) -> str:
    """
    Sanitize JSON string by removing unnecessary escape characters.

    Args:
        json_string: The JSON string to sanitize

    Returns:
        str: The sanitized JSON string
    """
    json_string = unescape(json_string)
    json_string = json_string.replace("\\\\", "\\")
    json_string = json_string.replace('\\"', '"')
    return json_string


def extract_json_from_html(html: str) -> dict[str, Any]:
    """
    Extract JSON data embedded in the HTML content.

    Args:
        html: The HTML content containing embedded JSON data

    Returns:
        dict: The extracted JSON data

    Raises:
        ValueError: If the JSON data cannot be found in the HTML
        json.JSONDecodeError: If the JSON data cannot be parsed
    """
    start_marker = 'kmtBoot.setProps("'
    end_marker = '");'

    start = html.find(start_marker)
    if start == -1:
        raise ValueError("Start marker not found")
    start += len(start_marker)

    end = html.find(end_marker, start)
    if end == -1:
        raise ValueError("End marker not found")

    htmljson = html[start:end]
    sanitized = sanitize_json_string(unescape(htmljson))

    try:
        result = json.loads(sanitized)
    except json.JSONDecodeError as e:
        # Provide detailed debugging information on failure
        print("Failed to decode JSON. Problematic string:")
        print(sanitized)
        raise e
    return result


def json_to_gpx(json_data: dict[str, Any]) -> gpxpy.gpx.GPX:
    """
    Convert JSON data to GPX format.

    Args:
        json_data: The JSON data containing tour information

    Returns:
        gpxpy.gpx.GPX: The GPX object

    Raises:
        ValueError: If the coordinates are empty or invalid
    """
    coordinates = json_data["page"]["_embedded"]["tour"]["_embedded"]["coordinates"]["items"]
    if not coordinates:
        raise ValueError("No coordinates found in tour data")

    gpx = gpxpy.gpx.GPX()
    gpx.name = json_data["page"]["_embedded"]["tour"]["name"]

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    for item in coordinates:
        lat = item["lat"]
        lng = item["lng"]
        alt = item["alt"]

        # Validate coordinates
        if not -90 <= lat <= 90 or not -180 <= lng <= 180:
            raise ValueError(f"Invalid coordinates: lat={lat}, lng={lng}")

        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lng, elevation=alt)
        )

    return gpx


def write_gpx(gpx: gpxpy.gpx.GPX, filename: str) -> None:
    """
    Write GPX data to a file.

    Args:
        gpx: The GPX object to write
        filename: The output file path

    Raises:
        IOError: If the file cannot be written
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(gpx.to_xml())


def main() -> None:
    """
    Main function to handle command-line interface and program flow.
    Downloads tour data from Komoot URL and saves it as a GPX file.
    """
    parser = argparse.ArgumentParser(description="Convert Komoot tour URL to GPX")
    parser.add_argument("url", help="The Komoot URL to make a GPX for")
    parser.add_argument("-o", "--output", required=True, help="The GPX file to create")
    args = parser.parse_args()

    try:
        html = make_http_request(args.url)
        extracted_data = extract_json_from_html(html)
        gpx = json_to_gpx(extracted_data)
        write_gpx(gpx, args.output)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except ValueError as e:
        print(f"Value error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except requests.RequestException as e:
        print(f"HTTP request error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except OSError as e:
        print(f"File system error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
