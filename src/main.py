import requests
import argparse
import json
from typing import Any
from html import unescape


def make_http_request(url: str) -> str:
    """
    Make an HTTP GET request and return the response content as a string.
    """
    headers = {"User-Agent": "komootgpx"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def extract_json_from_html(html: str) -> dict[str, Any]:
    """
    Extract JSON data embedded in the HTML content.
    """
    start_marker = "kmtBoot.setProps(\""
    end_marker = "\");"

    start = html.find(start_marker)
    if start == -1:
        raise ValueError("Start marker not found")
    start += len(start_marker)

    end = html.find(end_marker, start)
    if end == -1:
        raise ValueError("End marker not found")

    htmljson = html[start:end]
    unescaped = unescape(htmljson)
    result = json.loads(unescaped)
    return result


def main():
    pass

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert Komoot tour URL to GPX")
    parser.add_argument("url", help="The Komoot URL to make a GPX for")
    # parser.add_argument("-o", "--output", required=True, help="The GPX file to create")
    args = parser.parse_args()

    try:
        html = make_http_request(args.url)
        d = extract_json_from_html(html)
        print(d)
    except Exception as e:
        print(f"Error: {e}")

    main()
