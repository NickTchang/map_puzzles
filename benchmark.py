import subprocess
import sys
import itertools
import pandas as pd
import re
import time
from datetime import datetime

# config
MODULE_NAME = "map_puzzles.main"
OUTPUT_FILE = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# parameters
# keys must match the argparse arguments in your main.py
PARAM_GRID = {
    "n": [20, 40, 60],          # Compare complexity
    "iters": [1000, 5000],      # Compare heuristic depth
    "seed": [0, 1, 2, 3, 4],    # CRITICAL: 5 seeds per config for statistical significance
    "country": ["DE"],
    # Output path for the generated maps (keep them separate)
    "out-path": ["benchmark_maps/"] 
}

def parse_output(output: str) -> dict:
    """Scrapes the stdout from your main.py to extract metrics."""
    data = {}
    
    # Regex 1: "Instance generation took 1.23 seconds!"
    t_match = re.search(r"Instance generation took ([\d\.]+) seconds", output)
    if t_match:
        data["runtime_s"] = float(t_match.group(1))

    # Regex 2: "n=40 diff_edges(OPT\NN)=5 shared_edges=35"
    edge_match = re.search(r"diff_edges\(OPT\\NN\)=(\d+).*shared_edges=(\d+)", output)
    if edge_match:
        data["diff_edges"] = int(edge_match.group(1))
        data["shared_edges"] = int(edge_match.group(2))

    # Regex 3: "opt_len=123.456 pop_sum=500000"
    obj_match = re.search(r"opt_len=([\d\.]+).*pop_sum=([\d\.]+)", output)
    if obj_match:
        data["opt_len"] = float(obj_match.group(1))
        data["pop_sum"] = float(obj_match.group(2))
        
    return data

def run_benchmark():
    # Generate all combinations of parameters
    keys, values = zip(*PARAM_GRID.items())
    experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    results = []
    total = len(experiments)

    print(f"🚀 Starting benchmark of {total} experiments...")

    for i, params in enumerate(experiments):
        print(f"[{i+1}/{total}] Running: n={params['n']}, iters={params['iters']}, seed={params['seed']}...", end=" ", flush=True)
        
        # construct command: [python, -m, module, arg1, val1, ...]
        cmd = [sys.executable, "-m", MODULE_NAME]
        for k, v in params.items():
            cmd.extend([f"--{k}", str(v)])

        try:
            # Run the command and capture output
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the output
            metrics = parse_output(proc.stdout)
            
            # Combine inputs and outputs
            row = {**params, **metrics}
            results.append(row)
            print("✅ Done")

        except subprocess.CalledProcessError as e:
            print(f"Error!\nStderr: {e.stderr}")
        except Exception as e:
            print(f"Unexpected Error: {e}")

    # Save to CSV for analysis
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Benchmark complete. Data saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()