from . import db

def load_cities() -> None:
    df = db.load_cities_de()
    print(df.head(15))


if __name__ == "__main__":
    load_cities()
