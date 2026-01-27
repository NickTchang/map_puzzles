from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

# (lat, lng)
Coord = Tuple[float, float]
Coords = Dict[str, Coord]
Tour = List[str]
Edge_set = Set[Tuple[str, str]]


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
    return math.hypot(a[0] - b[0], a[1] - b[1])


def print_progress(prefix: str, curr: int, end: int) -> None:
    if curr == end:
        print(prefix + str(curr) + " Complete!")

    LINE_UP = "\033[1A"
    LINE_CLEAR = "\x1b[2K"
    print(prefix + str(curr) + " out of " + str(end))
    print(LINE_UP, end=LINE_CLEAR)
