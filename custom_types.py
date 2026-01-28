from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from pyproj import Transformer

# (lon, lat)
Coord = Tuple[float, float]
Coords = Dict[str, Coord]
Tour = List[str]
Edge_set = Set[Tuple[str, str]]

t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


@dataclass(frozen=True)
class InstanceProperty:
    # coordinates of the cities in the instance
    coords: Coords
    # sum of the total population
    pop_sum: float
    # optimal tour
    opt_tour: Tour
    # length of the optimal tour
    opt_len: float
    # length of the second shortes tour
    second_len: float
    # set of edges for each node to it's nearest node
    nn_graph: Edge_set
    # edges that are not in the NN graph
    diff_edges: float
    # the convex hull
    convex_hull: Tour
    # shotest edge in the graph
    min_dist: float


def better(a: InstanceProperty, b: InstanceProperty) -> bool:
    """
    Compares which instance is better.
    """
    if a.diff_edges != b.diff_edges:
        return a.diff_edges > b.diff_edges
    return a.pop_sum > b.pop_sum


def _euclidean_degrees(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """
    Takes in lonlat of two points and return their distance in km
    projects from EPSG:4326 to EPSG:3857
    """
    ax, ay = t.transform(a[0], a[1])
    bx, by = t.transform(b[0], b[1])
    return math.hypot(ax - bx, ay - by) / 1000


def print_progress(prefix: str, curr: int, end: int) -> None:
    if curr == end:
        print(prefix + str(curr) + " Complete!")

    LINE_UP = "\033[1A"
    LINE_CLEAR = "\x1b[2K"
    print(prefix + str(curr) + " out of " + str(end))
    print(LINE_UP, end=LINE_CLEAR)


def save_args(args, path="args.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for k, v in sorted(vars(args).items()):
            f.write(f"{k}={v!r}\n")
