from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from .custom_types import Coords

DEFAULT_URL: Final[str] = "https://simplemaps.com/static/data/country-cities/de/de.csv"

DEFAULT_GEONAMES_ZIP: Final[Path] = Path(__file__).resolve().parent / "cities5000.zip"
# DEFAULT_GEONAMES_ZIP_500: Final[Path] = Path(__file__).resolve().parent / "cities500.zip"
# DEFAULT_GEONAMES_ZI_1000: Final[Path] = Path(__file__).resolve().parent / "cities1000.zip"

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


def load_cities_all(path: str | Path = DEFAULT_GEONAMES_ZIP) -> pd.DataFrame:
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
    df["population"] = pd.to_numeric(
        df["population"].astype(str).str.strip(), errors="coerce"
    ).fillna(0)

    return df.reset_index(drop=True)


def load_cities_de(path: str | Path = DEFAULT_GEONAMES_ZIP) -> pd.DataFrame:
    """
    Load all german cities
    Returns a DataFrame with columns:
      city (str)
      lon (float)
      lat (float)
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
        (df["country_code"] == "DE")
        & (df["feature_class"] == "P")
        & (df["feature_code"] != "PPLX"),
        ["name", "longitude", "latitude", "population"],
    ].copy()

    df = df.rename(
        columns={
            "name": "city",
        }
    )

    df["city"] = df["city"].astype(str).str.strip()

    df["latitude"] = pd.to_numeric(
        df["latitude"].astype(str).str.strip(), errors="coerce"
    )
    df["longitude"] = pd.to_numeric(
        df["longitude"].astype(str).str.strip(), errors="coerce"
    )
    df["population"] = pd.to_numeric(
        df["population"].astype(str).str.strip(), errors="coerce"
    ).fillna(0)

    # remove invalide rows
    df = df.dropna(subset=["latitude", "longitude"])
    df = df.loc[df["city"] != ""].copy()

    # places with same name and less population are removed
    df = df.sort_values("population", ascending=False).drop_duplicates(subset=["city"])

    return df.reset_index(drop=True)


def to_coords(df: pd.DataFrame) -> Coords:
    coords: Coords = {}

    for city, lat, lon in df.loc[:, ["city", "latitude", "longitude"]].itertuples(
        index=False, name=None
    ):
        coords[str(city)] = (float(lon), float(lat))

    return coords
