import json
from pathlib import Path
import pandas as pd

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")
OUT = PROCESSED_PATH / "assets_daily.csv"

ASSET_TYPE = {
    "bitcoin": "crypto",
    "ethereum": "crypto",
    "brent_oil": "commodity",
    "sp500": "index",
    "nasdaq": "index",
}

def latest(pattern: str) -> Path:
    files = list(RAW_PATH.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files for {pattern}")
    return max(files, key=lambda f: f.stat().st_mtime)

def main():
    crypto_file = latest("crypto_hist_*.json")
    market_file = latest("market_hist_*.json")

    rows = []

    # crypto: list of [ms, price]
    crypto = json.loads(crypto_file.read_text(encoding="utf-8"))
    for asset, series in crypto["data"].items():
        for ms, price in series:
            dt = pd.to_datetime(ms, unit="ms", utc=True).date().isoformat()
            rows.append({"date": dt, "asset": asset, "asset_type": ASSET_TYPE.get(asset, "crypto"), "price_usd": float(price)})

    market = json.loads(market_file.read_text(encoding="utf-8"))
    for asset, series in market["data"].items():
        for item in series:
            rows.append({"date": item["date"], "asset": asset, "asset_type": ASSET_TYPE.get(asset, "unknown"), "price_usd": float(item["close"])})

    df = pd.DataFrame(rows).dropna()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.sort_values(["asset", "date"])

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved daily dataset: {OUT} with {len(df)} rows")

if __name__ == "__main__":
    main()