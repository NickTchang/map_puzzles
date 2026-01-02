from __future__ import annotations

from typing import Tuple
import folium

from .custom_types import Coords, Tour


def build_map(
    tour: Tour,
    coords: Coords,
    center: Tuple[float, float] = (51.1657, 10.4515),
    zoom_start: int = 4,
    line_color: str = "#fc4103",
) -> folium.Map:
    m = folium.Map(location=[center[0], center[1]], zoom_start=zoom_start)

    points = [coords[city] for city in tour]
    points.append(points[0])

    folium.PolyLine(points, color=line_color).add_to(m)

    for lat, lng in points[:-1]:
        folium.CircleMarker(
            location=[lat, lng],
            radius=7,
            fill=True,
            stroke=False,
            color=line_color,
            fill_opacity=0.8,
        ).add_to(m)

    return m


def save_map(m: folium.Map, path: str) -> None:
    m.save(path)
