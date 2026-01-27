from . import db


def print_de_cities() -> None:
    df = db.load_cities_de()
    df.sort_values(by=["population"], ascending=False)
    print(df.head(30))


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
    # print_de_cities()
    print_full_attributes()
