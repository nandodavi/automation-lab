import sqlite3
import pandas as pd
from pathlib import Path

print("LOAD STARTED")

PROCESSED_PATH = Path("data/processed/crypto_prices.csv")
DB_PATH = Path("data/crypto.db")


def load_to_database():
    if not PROCESSED_PATH.exists():
        raise FileNotFoundError("Processed CSV not found.")

    df = pd.read_csv(PROCESSED_PATH)

    conn = sqlite3.connect(DB_PATH)

    df.to_sql(
        "crypto_prices",
        conn,
        if_exists="append",
        index=False
    )

    conn.close()
    print("Data loaded into SQLite database successfully.")


if __name__ == "__main__":
    try:
        load_to_database()
    except Exception as e:
        print("ERROR:", e)