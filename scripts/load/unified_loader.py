import sqlite3
import pandas as pd
from pathlib import Path

PROCESSED_FILE = Path("data/processed/assets_prices.csv")
DB_PATH = Path("data/market.db")
TABLE = "asset_prices"

def ensure_table(conn: sqlite3.Connection):
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            asset TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            price_usd REAL NOT NULL,
            timestamp TEXT NOT NULL,
            source_file TEXT
        )
    """)
    # Prevent duplicates (same asset + timestamp)
    conn.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_asset_ts
        ON {TABLE} (asset, timestamp)
    """)

def load_incremental():
    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(f"Missing processed file: {PROCESSED_FILE}")

    df = pd.read_csv(PROCESSED_FILE)

    # Make sure timestamp is consistent text (ISO)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_table(conn)
        # Insert row by row with ignore duplicates
        rows = df.to_dict(orient="records")
        conn.executemany(
            f"""
            INSERT OR IGNORE INTO {TABLE} (asset, asset_type, price_usd, timestamp, source_file)
            VALUES (:asset, :asset_type, :price_usd, :timestamp, :source_file)
            """,
            rows
        )
        conn.commit()
        print(f"Loaded {len(rows)} rows into {DB_PATH} -> {TABLE} (duplicates ignored).")
    finally:
        conn.close()

if __name__ == "__main__":
    load_incremental()