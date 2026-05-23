from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

from .custom_types import Coords, InstanceProperty, _euclidean_degrees, print_progress
from .db import to_coords, to_coords_projected
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


def evaluate_instance(instance_df: pd.DataFrame) -> InstanceProperty:
    coords: Coords = to_coords(instance_df)
    coords_projeted: Coords = to_coords_projected(instance_df)

    # opt_tour = solve_tsp_gurobi(coords)
    opt_tour, opt_len, _, second_len = solve_tsp_gurobi_best_and_second_best(
        coords_projeted
    )

    nn_graph, min_dist = nearest_neighbor_graph(coords_projeted)

    diff_edges = diff_edges_count_tour_edgeset(opt_tour, nn_graph)
    pop_sum = _population_sum(instance_df)

    opt_len = tour_length(coords_projeted, opt_tour)

    _city_names = list(coords_projeted.keys())
    _coords = np.array([coords_projeted[name] for name in _city_names])

    hull = ConvexHull(_coords)
    hull_names = [_city_names[i] for i in hull.vertices]

    return InstanceProperty(
        min_dist=min_dist,
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
    pop_weight: float = 1.0,
    nn_diff_weight: float = 1.0,
    opt_diff_weight: float = 1.0,
    convex_hull_weight: float = 1.0,
    seed: int = 0,
    frames: Optional[List] = None,
    trace: Optional[List[Dict[str, float]]] = None,
) -> Tuple[pd.DataFrame, InstanceProperty]:
    """
    simulated annealing over a candidate pool by swapping cities
    """

    def get_subsetproperty(df: pd.DataFrame) -> InstanceProperty:
        key = tuple(sorted(df["city"].astype(str).tolist()))
        if key in cache:
            return cache[key]
        ev = evaluate_instance(df)
        cache[key] = ev
        return ev

    def score_terms(ip: InstanceProperty) -> Dict[str, float]:
        pop_norm = ip.pop_sum / pop_ref
        opt_diff = (ip.second_len - ip.opt_len) / (ip.opt_len * 0.05)
        convex_hull_ratio = 1 - (len(ip.convex_hull) / len(ip.coords))
        diff_edge_ratio = ip.diff_edges / len(ip.opt_tour)
        terms = {
            "nn_diff_term": nn_diff_weight * diff_edge_ratio,
            "pop_term": pop_weight * pop_norm,
            "opt_diff_term": opt_diff_weight * opt_diff,
            "convex_hull_term": convex_hull_weight * convex_hull_ratio,
        }
        terms["total"] = float(
            sum(terms.values())
        )  # * min(1.0, max(0.0, ip.min_dist / min_dist))
        return terms

    if n <= 2:
        raise ValueError("n must be >= 3 for a tour")

    if pool_size < n:
        raise ValueError(
            f"pool_size={pool_size} n={n}, pool_size must be larger than n"
        )

    rng = np.random.default_rng(seed)

    pool = (
        df_all.copy()
        # .assign(
        #     pop_num=pd.to_numeric(df_all["population"], errors="coerce").fillna(0.0)
        # )
        # .sort_values("pop_num", ascending=False)
        # .head(pool_size)
        # .drop(columns=["pop_num"])
        # .reset_index(drop=True)
    )
    pool_coords_projected = to_coords_projected(pool)

    if len(pool) < n:
        raise ValueError(f"pool_size={pool_size}, but df only has {len(pool)} rows.")

    # normalization factor for population,
    pop_ref = max(_population_sum(pool.head(n)), 1.0)
    # caching to save recomputing the same instance property
    cache: Dict[Tuple[str, ...], InstanceProperty] = {}

    # Start from a random sample
    # current_df = pool.sample(n, random_state=1).copy()
    current_df = pool.head(n).copy()
    current_property = get_subsetproperty(current_df)

    best_df = current_df.copy()
    best_property = current_property
    best_score = 0

    current_set = set(current_df["city"].astype(str).tolist())
    pool_cities = pool["city"].tolist()
    pool_indexed = pool.set_index("city", drop=False)

    # debug
    skipped_iter = 0
    # annealing
    T0 = 1.0
    T1 = 0.01

    for k in range(iters):
        t = k / max(1, iters - 1)
        T = T0 * ((T1 / T0) ** t)

        skipped_this_iter = False
        accepted_this_iter = False

        out_city = rng.choice(tuple(current_set))
        valid_choices = list(set(pool_cities) - current_set)

        others = current_set - {out_city}
        valid_choices = [
            c
            for c in valid_choices
            if min(
                _euclidean_degrees(pool_coords_projected[c], pool_coords_projected[o])
                for o in others
            )
            >= min_dist
        ]

        if not valid_choices:
            skipped_iter += 1
            skipped_this_iter = True
            continue
        #chose a random city from the valid choices based on the population, so that more populated cities are more likely to be chosen
        pop_preference_weights = np.array([pool_indexed.loc[c]["population"] for c in valid_choices])
        in_city = rng.choice(valid_choices, p=pop_preference_weights / pop_preference_weights.sum())

        candidate_set = set(current_set)
        candidate_set.remove(out_city)
        candidate_set.add(in_city)

        proposal = pool_indexed.loc[list(candidate_set)].reset_index(drop=True)

        try:
            candidate_property = get_subsetproperty(proposal)
        except Exception:
            skipped_this_iter = True
            continue

        # if candidate_property.diff_edges < min_diff_edges:
        #     skipped_this_iter = True
        #     continue

        current_score = score_terms(current_property)["total"]
        new_score = score_terms(candidate_property)["total"]

        accept = False
        if new_score >= current_score:
            accept = True
        else:
            delta = new_score - current_score
            accept = rng.random() < math.exp(delta / max(T, 1e-9))

        if accept:
            accepted_this_iter = True
            current_df = proposal
            current_property = candidate_property
            current_set = candidate_set

            # visualization
            if frames is not None:
                tour = current_property.opt_tour
                coords = current_property.coords
                pts = [list(coords[c]) for c in tour] + [list(coords[tour[0]])]
                frames.append(pts)

            # if better(current_property, best_property):
            #     best_df = current_df.copy()
            #     best_property = current_property

            if current_score > best_score:
                best_df = current_df.copy()
                best_property = current_property
                best_score = current_score

        # visualization
        if trace is not None:
            row = {
                "iter": k,
                "T": float(T),
                "accepted": int(accepted_this_iter),
                "skipped": int(skipped_this_iter),
            }
            row.update(score_terms(current_property))
            trace.append(row)

        # print progress:
        print_progress("Simulated annealing interations: ", k, iters)
    print("iteration skipped: " + str(skipped_iter))
    return best_df, best_property
