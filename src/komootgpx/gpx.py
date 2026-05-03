from __future__ import annotations

from pathlib import Path

import gpxpy.gpx

from .komoot import Tour


def tour_to_gpx(tour: Tour) -> gpxpy.gpx.GPX:
    gpx = gpxpy.gpx.GPX()
    gpx.name = tour.name

    track = gpxpy.gpx.GPXTrack()
    track.name = tour.name
    gpx.tracks.append(track)

    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    for coordinate in tour.coordinates:
        segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                latitude=coordinate.lat,
                longitude=coordinate.lng,
                elevation=coordinate.alt,
            )
        )

    return gpx


def write_gpx(gpx: gpxpy.gpx.GPX, output: str | Path) -> None:
    Path(output).write_text(gpx.to_xml(), encoding="utf-8")
