from . import db


def load_cities() -> None:
    df = db.load_cities_de()
    print(df)


def test_solver() -> None:
    pass


if __name__ == "__main__":
    load_cities()
