from __future__ import annotations

from datetime import datetime, timedelta

import folium
from folium.plugins import TimestampedGeoJson

from .custom_types import Coords, Edge_set, Tour


def add_tour(
    m: folium.Map,
    tour: Tour,
    coords: Coords,
    line_color: str = "#fc4103",
    opacity: float = 1,
) -> folium.Map:
    points = [(coords[city][1], coords[city][0]) for city in tour]
    points.append(points[0])

    folium.PolyLine(points, color=line_color, opacity=opacity).add_to(m)

    for lon, lat in points[:-1]:
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            fill=True,
            stroke=False,
            color=line_color,
            fill_opacity=opacity,
        ).add_to(m)

    return m


def add_edges(
    m: folium.Map,
    edges: Edge_set,
    coords: Coords,
    line_color: str = "#1f77b4",
    opacity: float = 0.6,
) -> folium.Map:
    edges_tuple = tuple(edges)
    for a, b in edges_tuple:
        folium.PolyLine(
            [(coords[a][1], coords[a][0]), (coords[b][1], coords[b][0])],
            color=line_color,
            opacity=opacity,
        ).add_to(m)

    return m


def build_map(
    tour: Tour,
    coords: Coords,
    zoom_start: int = 4,
) -> folium.Map:
    center_lat = 0
    center_lon = 0

    points = [coords[city] for city in tour]

    for lon, lat in points:
        center_lon += lon
        center_lat += lat

    center_lat = center_lat / len(tour)
    center_lon = center_lon / len(tour)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)

    return m


def save_map(m: folium.Map, path: str) -> None:
    m.save(path)


def add_SA_process(m, frames, keep_every=1):
    frames = frames[::keep_every]
    if not frames:
        raise ValueError("frames is empty")

    t0 = datetime(2020, 1, 1)
    features = []

    for i, pts_lonlat in enumerate(frames):
        coords_lonlat = [[lon, lat] for lon, lat in pts_lonlat]
        t = (t0 + timedelta(seconds=i)).isoformat()

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                "properties": {
                    "times": [t] * len(coords_lonlat),
                    "style": {"weight": 3, "color": "#fc4103"},
                },
            }
        )

    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT1S",
        duration="PT0S",
        add_last_point=False,
        auto_play=False,
        loop=False,
        time_slider_drag_update=True,
    ).add_to(m)
    return m
