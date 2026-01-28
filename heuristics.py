from __future__ import annotations

import random
from math import inf
from typing import Optional, Sequence, Tuple

from .custom_types import Coords, Edge_set, Tour, _euclidean_degrees


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


def tour_edges_undirected(tour: Sequence[str]) -> Edge_set:
    """
    undirected edge set for a Hamiltonian cycle.
    """
    n = len(tour)
    edges: Edge_set = set()
    for i in range(n):
        a = tour[i]
        b = tour[(i + 1) % n]
        edges.add((a, b) if a < b else (b, a))
    return edges


def diff_edges_count_tours(opt_tour: Sequence[str], heur_tour: Sequence[str]) -> int:
    """
    number of different edges in two tours
    """
    e_opt = tour_edges_undirected(opt_tour)
    e_heur = tour_edges_undirected(heur_tour)
    return len(e_opt - e_heur)


def diff_edges_count_tour_edgeset(opt_tour: Sequence[str], heur_graph: Edge_set) -> int:
    """
    number of different edges between a tour and a graph
    """
    e_opt = tour_edges_undirected(opt_tour)
    return len(e_opt - heur_graph)


def nearest_neighbor_graph(coords_projected: Coords) -> Tuple[Edge_set, float]:
    min_dist: float = inf
    nn_graph: Edge_set = set()
    cities = list(coords_projected.keys())
    for c in cities:
        neighbors = cities.copy()
        neighbors.remove(c)
        closest_nbr = None
        closest_nbr_dist = inf
        for n in neighbors:
            _dist = _euclidean_degrees(coords_projected[c], coords_projected[n])
            if _dist < closest_nbr_dist:
                closest_nbr_dist = _dist
                closest_nbr = n
            if _dist < min_dist:
                min_dist = _dist
        if closest_nbr is not None:
            nn_graph.add((c, closest_nbr) if c < closest_nbr else (closest_nbr, c))
    return nn_graph, min_dist


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
