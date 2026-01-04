from __future__ import annotations

from typing import Callable, Dict
import pandas as pd


Weights = Dict[str, float]


def score_row(row: pd.Series, weights: Weights) -> float:
    pop = row.get("population")
    pop_val = float(pop) if pop is not None and pd.notna(pop) else 0.0

    return weights.get("population", 1.0) * pop_val


def pick_top_n_cities(
    df: pd.DataFrame,
    n: int,
    weights: Weights,
    scorer: Callable[[pd.Series, Weights], float] = score_row,
) -> pd.DataFrame:

    scored = df.copy()
    scored["score"] = scored.apply(lambda r: scorer(r, weights), axis=1)
    scored = scored.sort_values("score", ascending=False).head(n)
    return scored
