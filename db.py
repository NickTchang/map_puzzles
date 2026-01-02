from __future__ import annotations

from typing import Final
import pandas as pd

from .custom_types import Coords


DEFAULT_URL: Final[str] = "https://simplemaps.com/static/data/country-cities/de/de.csv"


def load_cities_de(url: str = DEFAULT_URL) -> pd.DataFrame:
    df = pd.read_csv(url, usecols=["city", "lat", "lng", "population"], dtype=str)

    df["lat"] = df["lat"].astype(str).str.strip().str.replace(",", ".", regex=False)
    df["lng"] = df["lng"].astype(str).str.strip().str.replace(",", ".", regex=False)

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")

    df = df.dropna(subset=["lat", "lng"])

    df["population"] = pd.to_numeric(df["population"], errors="coerce")

    df["city"] = df["city"].astype(str).str.strip()

    df = df.loc[df["city"] != ""].copy()

    return df


def to_coords(df: pd.DataFrame) -> Coords:
    coords: Coords = {}

    for city, lat, lng in df.loc[:, ["city", "lat", "lng"]].itertuples(
        index=False, name=None
    ):
        coords[str(city)] = (float(lat), float(lng))

    return coords
