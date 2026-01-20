from __future__ import annotations

import folium

from .custom_types import Coords, Tour


def add_tour(
    m: folium.Map,
    tour: Tour,
    coords: Coords,
    line_color: str = "#fc4103",
    opacity: float = 1,
) -> folium.Map:
    points = [coords[city] for city in tour]
    points.append(points[0])

    folium.PolyLine(points, color=line_color, opacity=opacity).add_to(m)

    for lat, lng in points[:-1]:
        folium.CircleMarker(
            location=[lat, lng],
            radius=7,
            fill=True,
            stroke=False,
            color=line_color,
            fill_opacity=opacity,
        ).add_to(m)

    return m


def build_map(
    tour: Tour,
    coords: Coords,
    zoom_start: int = 4,
) -> folium.Map:
    center_lat = 0
    center_lng = 0

    points = [coords[city] for city in tour]

    for lat, lng in points:
        center_lat += lat
        center_lng += lng

    center_lat = center_lat / len(tour)
    center_lng = center_lng / len(tour)

    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start)

    return m


def save_map(m: folium.Map, path: str) -> None:
    m.save(path)
