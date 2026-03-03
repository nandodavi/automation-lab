import sqlite3
import pandas as pd
from pathlib import Path

DB = Path("data/market.db")
CSV = Path("data/processed/assets_daily.csv")
TABLE = "asset_daily"

def ensure(conn):
    conn.execute(f"""
      CREATE TABLE IF NOT EXISTS {TABLE} (
        date TEXT NOT NULL,
        asset TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        price_usd REAL NOT NULL,
        PRIMARY KEY (date, asset)
      )
    """)

def main():
    if not CSV.exists():
        raise FileNotFoundError(f"CSV not found: {CSV}. Run transform first.")

    df = pd.read_csv(CSV)
    conn = sqlite3.connect(DB)
    try:
        ensure(conn)
        rows = df.to_dict(orient="records")
        conn.executemany(
            f"INSERT OR REPLACE INTO {TABLE} (date, asset, asset_type, price_usd) "
            f"VALUES (:date, :asset, :asset_type, :price_usd)",
            rows
        )
        conn.commit()
        print(f"Loaded {len(rows)} rows into {TABLE}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()