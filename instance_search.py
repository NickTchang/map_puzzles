from __future__ import annotations

import math
import random
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

from .custom_types import (
    Coords,
    InstanceProperty,
    _euclidean_degrees,
    better,
    print_progress,
)
from .db import to_coords
from .heuristics import (
    diff_edges_count_tour_edgeset,
    nearest_neighbor_graph,
    tour_length,
)
from .solver import solve_tsp_gurobi_best_and_second_best


def _population_sum(df: pd.DataFrame) -> float:
    if "population" not in df.columns:
        return 0.0
    return float(
        pd.to_numeric(df["population"], errors="coerce").fillna(0).pow(2).sum()
    )


def evaluate_instance(
    instance_df: pd.DataFrame,
) -> InstanceProperty:
    coords: Coords = to_coords(instance_df)

    # opt_tour = solve_tsp_gurobi(coords)
    opt_tour, opt_len, _, second_len = solve_tsp_gurobi_best_and_second_best(coords)

    nn_graph = nearest_neighbor_graph(coords)

    diff_edges = diff_edges_count_tour_edgeset(opt_tour, nn_graph)
    pop_sum = _population_sum(instance_df)

    opt_len = tour_length(coords, opt_tour)

    _city_names = list(coords.keys())
    _coords = np.array([coords[name] for name in _city_names])

    hull = ConvexHull(_coords)

    hull_names = [_city_names[i] for i in hull.vertices]

    return InstanceProperty(
        coords=coords,
        diff_edges=diff_edges,
        pop_sum=pop_sum,
        opt_tour=opt_tour,
        nn_graph=nn_graph,
        opt_len=opt_len,
        second_len=second_len,
        convex_hull=hull_names,
    )


def search_best_instance(
    df_all: pd.DataFrame,
    *,
    min_dist=1.5,
    n: int = 40,
    pool_size: int = 250,
    iters: int = 1500,
    min_diff_edges: int = 0,
    pop_weight: float = 0.05,
    seed: int = 0,
) -> Tuple[pd.DataFrame, InstanceProperty]:
    """
    simulated annealing over a candidate pool by swapping cities
    maximizes the following (priority in order):
      1) number of different edges between opt and nn tours
      2) population sum
      2) difference between OPT and second best solution

    use a scalar score for probabilistic acceptance:
        score = diff_edges + pop_weight * (pop_sum / pop_ref)
    """

    def get_subsetproperty(df: pd.DataFrame) -> InstanceProperty:
        key = tuple(sorted(df["city"].astype(str).tolist()))
        if key in cache:
            return cache[key]
        ev = evaluate_instance(df)
        cache[key] = ev
        return ev

    def scalar_score(ip: InstanceProperty) -> float:
        pop_norm = ip.pop_sum / pop_ref
        tour_diff_factor = ip.second_len / ip.opt_len
        convex_hull_ratio = 1 - (len(ip.convex_hull) / len(ip.coords))
        return (
            float(ip.diff_edges)
            + (pop_weight * pop_norm)
            + tour_diff_factor
            + convex_hull_ratio
        )

    if n <= 2:
        raise ValueError("n must be >= 3 for a tour")

    if pool_size < n:
        raise ValueError(
            f"pool_size={pool_size} n={n}, pool_size must be larger than n"
        )

    rng = random.Random(seed)

    pool = (
        df_all.copy()
        .assign(
            pop_num=pd.to_numeric(df_all["population"], errors="coerce").fillna(0.0)
        )
        .sort_values("pop_num", ascending=False)
        # .head(pool_size)
        .drop(columns=["pop_num"])
        .reset_index(drop=True)
    )
    pool_coords = to_coords(pool)

    if len(pool) < n:
        raise ValueError(f"pool_size={pool_size}, but df only has {len(pool)} rows.")

    # normalization factor for population,
    pop_ref = max(_population_sum(pool.head(n)), 1.0)
    # caching to save recomputing the same instance property
    cache: Dict[Tuple[str, ...], InstanceProperty] = {}

    # Start from the population-best subset
    current_df = pool.head(n).copy()
    current_property = get_subsetproperty(current_df)
    best_df = current_df.copy()
    best_property = current_property

    current_set = set(current_df["city"].astype(str).tolist())
    pool_cities = pool["city"].tolist()
    pool_indexed = pool.set_index("city", drop=False)

    # Temperature schedule
    T0 = 1.0
    T1 = 0.01

    for k in range(iters):
        t = k / max(1, iters - 1)
        T = T0 * ((T1 / T0) ** t)

        out_city = rng.choice(tuple(current_set))
        others = current_set - {out_city}
        valid_choices = list(set(pool_cities) - current_set)
        valid_choices = [
            c
            for c in valid_choices
            if min(_euclidean_degrees(pool_coords[c], pool_coords[o]) for o in others)
            >= min_dist
        ]

        if not valid_choices:
            continue
        in_city = rng.choice(valid_choices)

        candidate_set = set(current_set)
        candidate_set.remove(out_city)
        candidate_set.add(in_city)

        proposal = pool_indexed.loc[list(candidate_set)].reset_index(drop=True)

        try:
            candidate_property = get_subsetproperty(proposal)
        except Exception:
            continue

        if candidate_property.diff_edges < min_diff_edges:
            continue

        cur_s = scalar_score(current_property)
        new_s = scalar_score(candidate_property)

        accept = False
        if new_s >= cur_s:
            accept = True
        else:
            # annealing
            delta = new_s - cur_s
            accept = rng.random() < math.exp(delta / max(T, 1e-9))

        if accept:
            current_df = proposal
            current_property = candidate_property
            current_set = candidate_set

            if better(current_property, best_property):
                best_df = current_df.copy()
                best_property = current_property

        # print progress:
        print_progress("Simulated annealing interations: ", k, iters)
    return best_df, best_property
