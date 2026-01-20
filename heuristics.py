from __future__ import annotations

import random
from typing import Optional, Sequence, Set, Tuple

from .custom_types import Coords, Tour, _euclidean_degrees


def tour_length(coords: Coords, tour: Sequence[str]) -> float:
    n = len(tour)
    if n <= 1:
        return 0.0
    total = 0.0
    for i in range(n):
        a = coords[tour[i]]
        b = coords[tour[(i + 1) % n]]
        total += _euclidean_degrees(a, b)
    return total


def tour_edges_undirected(tour: Sequence[str]) -> Set[Tuple[str, str]]:
    """
    undirected edge set for a Hamiltonian cycle.
    (min,max) makes (a,b) == (b,a).
    """
    n = len(tour)
    edges: Set[Tuple[str, str]] = set()
    for i in range(n):
        a = tour[i]
        b = tour[(i + 1) % n]
        edges.add((a, b) if a < b else (b, a))
    return edges


def diff_edges_count(opt_tour: Sequence[str], heur_tour: Sequence[str]) -> int:
    """
    number of different edges in two tours
    """
    e_opt = tour_edges_undirected(opt_tour)
    e_heur = tour_edges_undirected(heur_tour)
    return len(e_opt - e_heur)


def nearest_neighbor_tour(coords: Coords, start: str) -> Tour:
    cities = list(coords.keys())
    if start not in coords:
        raise KeyError(f"start city {start!r} not in coords")

    unvisited = set(cities)
    unvisited.remove(start)

    tour: Tour = [start]
    cur = start

    while unvisited:
        cur_coord = coords[cur]
        nxt = min(unvisited, key=lambda c: _euclidean_degrees(cur_coord, coords[c]))
        tour.append(nxt)
        unvisited.remove(nxt)
        cur = nxt

    return tour


def nearest_neighbor_best_of_starts(
    coords: Coords,
) -> Tour:
    """
    runs NN randomly from half the starting cities and returns the shortest NN tour found
    """
    cities = list(coords.keys())
    k = int(len(cities) / 2)
    rng = random.Random(0)
    starts = rng.sample(cities, k=k)

    best_tour: Optional[Tour] = None
    best_len = float("inf")

    for s in starts:
        t = nearest_neighbor_tour(coords, start=s)
        L = tour_length(coords, t)
        if L < best_len:
            best_len = L
            best_tour = t

    assert best_tour is not None
    return best_tour
