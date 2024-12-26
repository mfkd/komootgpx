import requests
import argparse
import json
import traceback
import sys
from typing import Any
from html import unescape
import re
import gpxpy
import gpxpy.gpx


def make_http_request(url: str) -> str:
    """
    Make an HTTP GET request and return the response content as a string.
    """
    headers = {"User-Agent": "komootgpx"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def sanitize_json_string(json_string: str) -> str:
    json_string = unescape(json_string)
    json_string = json_string.replace("\\\\", "\\")
    json_string = json_string.replace('\\"', '"')
    return json_string


def extract_json_from_html(html: str) -> dict[str, Any]:
    """
    Extract JSON data embedded in the HTML content.
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
    """
    # TODO: Check gpx if coordinates are empty or invalid.
    gpx = gpxpy.gpx.GPX()

    gpx.name = json_data["page"]["_embedded"]["tour"]["name"]

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    for item in json_data["page"]["_embedded"]["tour"]["_embedded"]["coordinates"]["items"]:
        lat = item["lat"]
        lng = item["lng"]
        alt = item["alt"]
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lng, elevation=alt))

    return gpx

def write_gpx(gpx: gpxpy.gpx.GPX, filename: str) -> None:
    """
    Write GPX data to a file.
    """
    with open(filename, "w") as f:
        f.write(gpx.to_xml())



def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert Komoot tour URL to GPX")
    parser.add_argument("url", help="The Komoot URL to make a GPX for")
    parser.add_argument("-o", "--output", required=True, help="The GPX file to create")
    args = parser.parse_args()

    try:
        html = make_http_request(args.url)
        extracted_data = extract_json_from_html(html)
        gpx = json_to_gpx(extracted_data)
        write_gpx(gpx, args.output)
    except requests.RequestException as e:
        print(f"HTTP request error: {e}")
        traceback.print_exc()  # Log full traceback for debugging
        sys.exit(1)
    except ValueError as e:
        print(f"Value error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
