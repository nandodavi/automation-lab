import json
from pathlib import Path
import pandas as pd

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")
OUTPUT_FILE = PROCESSED_PATH / "assets_prices.csv"

ASSET_TYPE = {
    "bitcoin": "crypto",
    "ethereum": "crypto",
    "brent_oil": "commodity",
    "sp500": "index",
    "nasdaq": "index",
}

def parse_file(file_path: Path) -> pd.DataFrame:
    with open(file_path, "r") as f:
        data = json.load(f)

    timestamp = data.pop("timestamp", None)
    if timestamp is None:
        raise ValueError(f"Missing timestamp in {file_path.name}")

    rows = []
    for asset, payload in data.items():
        price = payload.get("usd")
        rows.append({
            "asset": asset,
            "asset_type": ASSET_TYPE.get(asset, "unknown"),
            "price_usd": float(price) if price is not None else None,
            "timestamp": timestamp,
            "source_file": file_path.name
        })

    return pd.DataFrame(rows)

def get_latest(pattern: str) -> Path:
    files = list(RAW_PATH.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No raw files found for {pattern} in {RAW_PATH.resolve()}")
    return max(files, key=lambda f: f.stat().st_mtime)

def save(df: pd.DataFrame):
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    if OUTPUT_FILE.exists():
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(OUTPUT_FILE, index=False)

def main():
    latest_crypto = get_latest("crypto_*.json")
    latest_market = get_latest("market_*.json")

    df = pd.concat([parse_file(latest_crypto), parse_file(latest_market)], ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", utc=True)

    save(df)
    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()