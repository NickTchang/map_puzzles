from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from .custom_types import Coords

DEFAULT_URL: Final[str] = "https://simplemaps.com/static/data/country-cities/de/de.csv"
DEFAULT_GEONAMES_ZIP: Final[Path] = Path(__file__).resolve().parent / "cities500.zip"

GEONAMES_COLUMNS: Final[list[str]] = [
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "latitude",
    "longitude",
    "feature_class",
    "feature_code",
    "country_code",
    "cc2",
    "admin1_code",
    "admin2_code",
    "admin3_code",
    "admin4_code",
    "population",
    "elevation",
    "dem",
    "timezone",
    "modification_date",
]


def load_cities_de(path: str | Path = DEFAULT_GEONAMES_ZIP) -> pd.DataFrame:
    """
    Load all german cities
    Returns a DataFrame with columns:
      city (str)
      lat (float)
      lng (float)
      population (int/float)
    """
    path = Path(path)

    df = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=GEONAMES_COLUMNS,
        compression="zip",
        dtype=str,
        encoding="utf-8",
        low_memory=False,
    )

    # filter for germany
    df = df.loc[
        df["country_code"] == "DE", ["name", "latitude", "longitude", "population"]
    ].copy()

    df = df.rename(
        columns={
            "name": "city",
            "latitude": "lat",
            "longitude": "lng",
        }
    )

    df["city"] = df["city"].astype(str).str.strip()

    df["lat"] = pd.to_numeric(df["lat"].astype(str).str.strip(), errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"].astype(str).str.strip(), errors="coerce")
    df["population"] = pd.to_numeric(
        df["population"].astype(str).str.strip(), errors="coerce"
    ).fillna(0)

    # remove invalide rows
    df = df.dropna(subset=["lat", "lng"])
    df = df.loc[df["city"] != ""].copy()

    # places with same name and less population are removed
    df = df.sort_values("population", ascending=False).drop_duplicates(subset=["city"])

    return df.reset_index(drop=True)


# def load_cities_de(url: str = DEFAULT_URL) -> pd.DataFrame:
#     df = pd.read_csv(url, usecols=["city", "lat", "lng", "population"], dtype=str)
#
#     df["lat"] = df["lat"].astype(str).str.strip().str.replace(",", ".", regex=False)
#     df["lng"] = df["lng"].astype(str).str.strip().str.replace(",", ".", regex=False)
#
#     df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
#     df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
#
#     df = df.dropna(subset=["lat", "lng"])
#
#     df["population"] = pd.to_numeric(df["population"], errors="coerce").fillna(0)
#
#     df["city"] = df["city"].astype(str).str.strip()
#
#     df = df.loc[df["city"] != ""].copy()
#
#     return df


def to_coords(df: pd.DataFrame) -> Coords:
    coords: Coords = {}

    for city, lat, lng in df.loc[:, ["city", "lat", "lng"]].itertuples(
        index=False, name=None
    ):
        coords[str(city)] = (float(lat), float(lng))

    return coords
