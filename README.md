# Komootgpx

Komootgpx creates a [GPX](https://en.wikipedia.org/wiki/GPS_Exchange_Format) file
from a public Komoot tour page.

## Install

Create a virtual environment, then install the CLI from the project root:

```shell
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Usage

Create a GPX file from a Komoot tour link:

```shell
komootgpx https://www.komoot.com/smarttour/33303609 -o route.gpx
```

For local development, the compatibility entrypoint still works:

```shell
python src/main.py https://www.komoot.com/smarttour/33303609 -o route.gpx
```

Use `--verbose` to show tracebacks when debugging parser or network failures.

## Development

Run the test suite with:

```shell
python -m unittest discover -s tests
```

The default suite includes a sanitized fixture captured from the public example
tour so parser and GPX conversion behavior are checked against realistic Komoot
payload shape without depending on Komoot during CI.

Run the optional live integration test against a public tour with:

```shell
KOMOOTGPX_LIVE_URL=https://www.komoot.com/smarttour/33303609 python -m unittest tests.test_live_komoot
```

## Limitations

Komootgpx reads the public tour data embedded in Komoot's HTML. Private tours,
authenticated access, and recovery from major Komoot page format changes are out
of scope; the CLI should fail clearly when those cases are encountered.
