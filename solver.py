from __future__ import annotations

import math
from itertools import combinations
from typing import Dict, List, Optional, Tuple

import gurobipy as gp
from gurobipy import GRB

from .custom_types import Coords, Tour


def _euclidean_degrees(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _build_distances(cities: List[str], coords: Coords) -> Dict[Tuple[str, str], float]:
    return {
        (i, j): _euclidean_degrees(coords[i], coords[j])
        for i, j in combinations(cities, 2)
    }


def _edges_to_ordered_tour(
    cities: List[str], selected_edges: List[Tuple[str, str]]
) -> Tour:
    adj: Dict[str, List[str]] = {c: [] for c in cities}
    for i, j in selected_edges:
        adj[i].append(j)
        adj[j].append(i)

    start = cities[0]
    tour = [start]
    prev = None
    cur = start

    while True:
        n0, n1 = adj[cur][0], adj[cur][1]
        nxt = n0 if n0 != prev else n1
        if nxt == start:
            break
        tour.append(nxt)
        prev, cur = cur, nxt

        if len(tour) > len(cities):
            raise RuntimeError(
                "Tour reconstruction exceeded city count (invalid edge set)."
            )

    if len(tour) != len(cities):
        raise RuntimeError("Did not reconstruct a full tour (subtour remained).")
    return tour


def solve_tsp_gurobi(
    coords: Coords,
    time_limit_s: Optional[float] = None,
) -> Tour:
    cities = list(coords.keys())
    dist_undirected = _build_distances(cities, coords)

    m = gp.Model("tsp")
    m.Params.LazyConstraints = 1
    if time_limit_s is not None:
        m.Params.TimeLimit = float(time_limit_s)

    x = m.addVars(
        dist_undirected.keys(), obj=dist_undirected, vtype=GRB.BINARY, name="x"
    )
    x.update({(j, i): x[i, j] for (i, j) in dist_undirected.keys()})

    m.addConstrs((x.sum(c, "*") == 2 for c in cities), name="deg2")

    def _subtour(edges: gp.tuplelist) -> List[str]:
        unvisited = cities[:]
        cycle = cities[:]  # Dummy - guaranteed to be replaced
        while unvisited:  # true if list is non-empty
            thiscycle = []
            neighbors = unvisited
            while neighbors:
                current = neighbors[0]
                thiscycle.append(current)
                unvisited.remove(current)
                neighbors = [j for _, j in edges.select(current, "*") if j in unvisited]
            if len(thiscycle) <= len(cycle):
                cycle = thiscycle  # New shortest subtour
        return cycle

    def _subtourelim(model: gp.Model, where: int) -> None:
        if where == GRB.Callback.MIPSOL:
            # make a list of edges selected in the solution
            vals = model.cbGetSolution(model._vars)
            selected = gp.tuplelist(
                (i, j) for i, j in model._vars.keys() if vals[i, j] > 0.5
            )
            # find the shortest cycle in the selected edge list
            tour = _subtour(selected)
            if len(tour) < len(cities):
                # add subtour elimination constr. for every pair of cities in subtour
                model.cbLazy(
                    gp.quicksum(model._vars[i, j] for i, j in combinations(tour, 2))
                    <= len(tour) - 1
                )

    m._x = x

    m.optimize(_subtourelim)

    if m.Status not in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL):
        raise RuntimeError(f"Gurobi ended with status {m.Status}.")

    vals = m.getAttr("x", x)
    selected_undirected = [
        (i, j) for (i, j) in dist_undirected.keys() if vals[i, j] > 0.5
    ]

    tour = _edges_to_ordered_tour(cities, selected_undirected)
    return tour
