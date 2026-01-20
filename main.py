from __future__ import annotations

import argparse
import time
from datetime import datetime

from .db import load_cities_de, to_coords
from .heuristics import diff_edges_count, nearest_neighbor_best_of_starts, tour_length
from .instance_search import search_best_instance
from .solver import solve_tsp_gurobi
from .visualizer import add_tour, build_map, save_map


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        type=str,
        default="tsp_map",
        help="Output file name without file extention, default = tsp_map",
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
        "--nn-starts",
        type=int,
        default=20,
        help="How many different start cities to try for NN, best NN tour is kept",
    )
    p.add_argument(
        "--pop-weight",
        type=float,
        default=0.05,
        help="Population weight (to make edges outweigh population, keep < 1)",
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
    return p.parse_args()


def main() -> None:
    args = parse_args()

    df = load_cities_de()

    chosen, _ = search_best_instance(
        df,
        n=args.n,
        min_dist=1,
        pool_size=args.pool_size,
        iters=args.iters,
        min_diff_edges=args.min_diff_edges,
        seed=args.seed,
        pop_weight=args.pop_weight,
    )

    coords = to_coords(chosen)
    opt_tour = solve_tsp_gurobi(coords)
    nn_tour = nearest_neighbor_best_of_starts(coords)

    diff_edges = diff_edges_count(opt_tour, nn_tour)
    shared_edges = len(opt_tour) - diff_edges
    opt_len = tour_length(coords, opt_tour)
    nn_len = tour_length(coords, nn_tour)

    pop_sum = float(
        __import__("pandas")
        .to_numeric(chosen.get("population"), errors="coerce")
        .fillna(0)
        .sum()
    )

    print(
        f"n={len(opt_tour)}  diff_edges(OPT\\NN)={diff_edges}  shared_edges={shared_edges}"
    )
    print(f"opt_len={opt_len:.3f}  nn_len={nn_len:.3f}  pop_sum={pop_sum:.0f}")
    # for i in opt_tour:
    #     print(i)

    m = build_map(opt_tour, coords)
    # nn tour
    add_tour(m, nn_tour, coords, line_color="#1f77b4", opacity=0.6)
    # opt tour
    add_tour(m, opt_tour, coords, line_color="#fc4103", opacity=1)

    # save all the stuff
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_map(m, args.out + "_n" + str(args.n) + "_" + current_datetime + ".html")
    chosen.to_csv(
        args.out + "_n" + str(args.n) + "_" + current_datetime + ".csv", index=False
    )


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    duration = end - start
    print("Instance generation took " + str(round(duration, 3)) + " seconds!")
