from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

import gurobipy as gp
from gurobipy import GRB

from .custom_types import Coords, Tour, _euclidean_degrees


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
) -> Tour:
    cities = list(coords.keys())
    dist_undirected = _build_distances(cities, coords)

    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        with gp.Model(env=env) as m:
            # Variables: is city 'i' adjacent to city 'j' on the tour?
            vars = m.addVars(
                dist_undirected.keys(), obj=dist_undirected, vtype=GRB.BINARY, name="x"
            )

            # Symmetric direction: use dict.update to alias variable with new key
            vars.update({(j, i): vars[i, j] for i, j in vars.keys()})

            # Constraints: two edges incident to each city
            m.addConstrs(vars.sum(c, "*") == 2 for c in cities)

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
                        neighbors = [
                            j for _, j in edges.select(current, "*") if j in unvisited
                        ]
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
                            gp.quicksum(
                                model._vars[i, j] for i, j in combinations(tour, 2)
                            )
                            <= len(tour) - 1
                        )

            m._vars = vars
            m.Params.LazyConstraints = 1
            m.optimize(_subtourelim)

            vals = m.getAttr("x", vars)
            selected_undirected = [
                (i, j) for (i, j) in dist_undirected.keys() if vals[i, j] > 0.5
            ]

            tour = _edges_to_ordered_tour(cities, selected_undirected)
    return tour


def solve_tsp_gurobi_best_and_second_best(
    coords: Coords,
) -> Tuple[Tour, float, Tour, float]:
    strict_obj_tol: float = 1e-6
    cities = list(coords.keys())
    dist_undirected = _build_distances(cities, coords)

    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        with gp.Model(env=env) as m:
            # Edge variables (undirected keys) + symmetric aliases for convenience in constraints/callback.
            vars = m.addVars(dist_undirected.keys(), vtype=GRB.BINARY, name="x")
            vars.update({(j, i): vars[i, j] for i, j in list(dist_undirected.keys())})

            # Degree constraints (2 incident edges per city)
            m.addConstrs(vars.sum(c, "*") == 2 for c in cities)

            # Build an objective expression that counts EACH undirected edge ONCE.
            obj_expr = gp.quicksum(
                dist_undirected[i, j] * vars[i, j] for (i, j) in dist_undirected.keys()
            )
            m.setObjective(obj_expr, GRB.MINIMIZE)

            def _subtour(edges: gp.tuplelist) -> List[str]:
                unvisited = cities[:]
                cycle = cities[:]
                while unvisited:
                    thiscycle = []
                    neighbors = unvisited
                    while neighbors:
                        current = neighbors[0]
                        thiscycle.append(current)
                        unvisited.remove(current)
                        neighbors = [
                            j for _, j in edges.select(current, "*") if j in unvisited
                        ]
                    if len(thiscycle) <= len(cycle):
                        cycle = thiscycle
                return cycle

            def _subtourelim(model: gp.Model, where: int) -> None:
                if where == GRB.Callback.MIPSOL:
                    vals = model.cbGetSolution(model._vars)
                    selected = gp.tuplelist(
                        (i, j) for (i, j) in model._vars.keys() if vals[i, j] > 0.5
                    )
                    tour = _subtour(selected)
                    if len(tour) < len(cities):
                        model.cbLazy(
                            gp.quicksum(
                                model._vars[i, j] for i, j in combinations(tour, 2)
                            )
                            <= len(tour) - 1
                        )

            m._vars = vars
            m.Params.LazyConstraints = 1

            # Optimal
            m.optimize(_subtourelim)
            if m.Status != GRB.OPTIMAL:
                raise RuntimeError(
                    f"Optimal solve did not finish to optimality (status={m.Status})."
                )

            opt_len = float(m.ObjVal)
            best_edges = [
                (i, j) for (i, j) in dist_undirected.keys() if vars[i, j].X > 0.5
            ]
            opt_tour = _edges_to_ordered_tour(cities, best_edges)

            # find second best objective, excluding ties to the optimum
            tol = float(strict_obj_tol) * max(1.0, abs(opt_len))
            m.addConstr(obj_expr >= opt_len + tol, name="force_next_longer")

            m.optimize(_subtourelim)
            if m.Status != GRB.OPTIMAL:
                raise RuntimeError(
                    f"Second-best solve did not finish to optimality (status={m.Status}). "
                    "If INFEASIBLE, it means no tour is strictly longer under the chosen tolerance."
                )

            second_len = float(m.ObjVal)
            second_edges = [
                (i, j) for (i, j) in dist_undirected.keys() if vars[i, j].X > 0.5
            ]
            second_tour = _edges_to_ordered_tour(cities, second_edges)

    return opt_tour, opt_len, second_tour, second_len
