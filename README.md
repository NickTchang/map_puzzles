# Map-Puzzle-Generator

A Python command line tool for generating **Travelling Salesman Problem (TSP) puzzle instances** based on real-world city data. It selects a set of cities from a given country, finds the optimal tour using Gurobi, and renders the result as an interactive map.

## Requirements

- Python 3.x
- Gurobi (requires a valid license)
- Dependencies listed in `requirements.txt`
- (recommend using a virtual environment)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run as a Python module from the repo root:

```bash
py -m map_puzzles.main --n 40
```

### Key options

| Flag | Default | Description |
|---|---|---|
| `--n` | `40` | Number of cities in the puzzle |
| `--country` | `DE` | Country code (e.g. `DE`, `FR`, `US`) |
| `--min-dist` | `50.0` | Minimum distance between cities (km) |
| `--iters` | `3000` | Simulated annealing iterations |
| `--seed` | `0` | Random seed for reproducibility |
| `--out` | `tsp_map` | Output filename (no extension) |
| `--out-path` | `map_puzzle_build/` | Output folder |
| `--record` | `false` | Save a step-by-step animation of the SA process |

### Output

Each run creates a timestamped folder under `map_puzzle_build/` containing:

- `*.html` — interactive map with the optimal tour
- `*_nn.html` — map showing the nearest-neighbor graph
- `*.csv` — the selected cities with coordinates and population
- `*.txt` — the parameters used for the run
- `*_record.html` *(if `--record`)* — animated SA process
- `*_sa_trace.pdf` *(if `--record`)* — objective function trace plot

## Project structure

```
map_puzzles/
├── main.py            # CLI entry point
├── db.py              # City data loading and coordinate projection
├── instance_search.py # Simulated annealing city selection
├── solver.py          # Gurobi TSP solver
├── heuristics.py      # Nearest-neighbor heuristic
├── visualizer.py      # Folium map rendering
├── custom_types.py    # Shared type definitions
├── benchmark.py       # Benchmarking utilities
└── data/              # Bundled city datasets
```

## Data sources

- [GeoNames cities500/1000/5000](https://www.geonames.org/) (bundled as zip files)
