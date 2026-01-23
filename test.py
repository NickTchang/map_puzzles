from . import db


def load_cities() -> None:
    df = db.load_cities_de()
    df.sort_values(by=["population"], ascending=False)
    print(df.head(30))


def test_solver() -> None:
    pass


if __name__ == "__main__":
    load_cities()
