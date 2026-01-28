from __future__ import annotations

import argparse
import os
import time
from datetime import datetime

from .custom_types import save_args
from .db import load_cities_de, to_coords
from .heuristics import (
    diff_edges_count_tour_edgeset,
    nearest_neighbor_graph,
    tour_length,
)
from .instance_search import search_best_instance
from .solver import solve_tsp_gurobi
from .visualizer import add_edges, add_SA_process, add_tour, build_map, save_map


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        type=str,
        default="tsp_map",
        help="Output file name without file extention, default = tsp_map",
    )
    p.add_argument(
        "--out-path",
        type=str,
        default="map_puzzle_build/",
        help="folder path at which to save the generated instance, default = map_puzzle_build",
    )
    p.add_argument(
        "--pool-size",
        type=int,
        default=250,
        help="Pool size of the candidates for swapping",
    )
    p.add_argument(
        "--iters",
        type=int,
        default=3000,
        help="Number of iterations for the simulated annealing",
    )
    p.add_argument(
        "--min-diff-edges",
        type=int,
        default=0,
        help="Minimum number of edges different to Nearest-Neighbor heuristic",
    )
    p.add_argument(
        "--n",
        type=int,
        default=40,
        help="Number of cities",
    )
    p.add_argument(
        "--pop-weight",
        type=float,
        default=1.0,
        help="Population weight (to make edges outweigh population, keep < 1)",
    )
    p.add_argument(
        "--min-dist",
        type=float,
        default=50.0,
        help="Minimum distance between cities in kilometers",
    )
    p.add_argument(
        "--seed", type=int, default=0, help="Seed for the random number generator"
    )
    p.add_argument(
        "--instance-out",
        type=str,
        default="tsp_map.csv",
        help="csv file name as CSV(cities/coords/population) ",
    )
    p.add_argument(
        "--record",
        action="store_true",
        default=False,
        help="Display each of the simulated annealing step",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    df = load_cities_de()

    frames = []
    chosen, _ = search_best_instance(
        df,
        n=args.n,
        min_dist=args.min_dist,
        pool_size=args.pool_size,
        iters=args.iters,
        min_diff_edges=args.min_diff_edges,
        seed=args.seed,
        pop_weight=args.pop_weight,
        frames=frames,
        record=args.record,
    )

    coords = to_coords(chosen)
    opt_tour = solve_tsp_gurobi(coords)
    nn_graph, _ = nearest_neighbor_graph(coords)

    diff_edges = diff_edges_count_tour_edgeset(opt_tour, nn_graph)
    shared_edges = len(opt_tour) - diff_edges
    opt_len = tour_length(coords, opt_tour)

    pop_sum = float(
        __import__("pandas")
        .to_numeric(chosen.get("population"), errors="coerce")
        .fillna(0)
        .sum()
    )

    print(
        f"n={len(opt_tour)}  diff_edges(OPT\\NN)={diff_edges}  shared_edges={shared_edges}"
    )
    print(f"opt_len={opt_len:.3f}  pop_sum={pop_sum:.0f}")
    # for i in opt_tour:
    #     print(i)

    m = build_map(opt_tour, coords)
    # nn tour
    # add_tour(m, nn_graph, coords, line_color="#1f77b4", opacity=0.6)
    # opt tour
    add_edges(m, nn_graph, coords, opacity=0.6)
    add_tour(m, opt_tour, coords, line_color="#fc4103", opacity=1)

    # save all the stuff
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = (
        args.out_path
        + args.out
        + "_n"
        + str(args.n)
        + "_"
        + current_datetime
        + "/"
        + "n"
        + str(args.n)
        + "_"
        + current_datetime
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    save_map(
        m,
        file_path + ".html",
    )
    chosen.to_csv(
        file_path + ".csv",
        index=False,
    )

    # parameter logs
    save_args(
        args,
        file_path + ".txt",
    )

    if args.record:
        record_m = build_map(opt_tour, coords)
        add_SA_process(record_m, frames, 1)
        # save all the stuff
        save_map(
            record_m,
            file_path + "_record" + ".html",
        )


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    duration = end - start
    print("Instance generation took " + str(round(duration, 3)) + " seconds!")
