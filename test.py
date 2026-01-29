from . import db
import argparse


def print_country_cities(n:int = 10, country_code:str = "DE") -> None:
    df = db.load_cities_country(country_code=country_code)
    df.sort_values(by=["population"], ascending=False)
    print(df.head(n))

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--country",
        type=str,
        default="DE",
        help="Country code",
    )
    p.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of cities",
    )
    return p.parse_args()

def print_full_attributes() -> None:
    df = db.load_cities_all()
    df = df.loc[
        df["country_code"] == "DE",
        [
            # "geonameid",
            "name",
            # "asciiname",
            # "alternatenames",
            # "latitude",
            # "longitude",
            "feature_class",
            "feature_code",
            "country_code",
            # "cc2",
            "admin1_code",
            "admin2_code",
            "admin3_code",
            "admin4_code",
            "population",
            # "elevation",
            # "dem",
            # "timezone",
            # "modification_date",
        ],
    ].copy()
    df = df.sort_values(by=["population"], ascending=False)
    print(df.head(15))


def test_solver() -> None:
    pass


if __name__ == "__main__":
    args = parse_args()
    print_country_cities(n = args.n, country_code=args.country)
    # print_full_attributes()
