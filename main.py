from __future__ import annotations

import argparse

from .db import load_cities_de, to_coords, DEFAULT_URL
from .weights import pick_top_n_cities
from .solver import solve_tsp_gurobi
from .visualizer import build_map, save_map


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--url", type=str, default=DEFAULT_URL)
    p.add_argument(
        "--n",
        type=int,
        default=15,
        help="number of cities to select before solving TSP",
    )
    p.add_argument("--out", type=str, default="tsp_map.html")
    p.add_argument("--time-limit", type=float, default=None)
    p.add_argument("--quiet", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    df = load_cities_de(args.url)

    weights = {"population": 1.0}
    chosen = pick_top_n_cities(df, n=args.n, weights=weights)

    coords = to_coords(chosen)

    tour, obj = solve_tsp_gurobi(coords, time_limit_s=args.time_limit)

    m = build_map(tour, coords)
    save_map(m, args.out)

    if not args.quiet:
        print(f"Tour length objective: {obj}")
        print(f"Wrote map: {args.out}")


if __name__ == "__main__":
    main()
