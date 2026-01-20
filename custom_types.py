from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

# (lat, lng)
Coord = Tuple[float, float]
Coords = Dict[str, Coord]
Tour = List[str]


@dataclass(frozen=True)
class InstanceProperty:
    diff_edges: int
    pop_sum: float
    opt_tour: Tour
    nn_tour: Tour
    opt_len: float
    second_len: float
    nn_len: float


def better(a: InstanceProperty, b: InstanceProperty) -> bool:
    """
    Compares which instance is better.
    """
    if a.diff_edges != b.diff_edges:
        return a.diff_edges > b.diff_edges
    return a.pop_sum > b.pop_sum


def _euclidean_degrees(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
