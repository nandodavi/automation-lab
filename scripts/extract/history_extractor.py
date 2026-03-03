import json
import requests
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf

RAW_PATH = Path("data/raw")
DAYS = 15

CRYPTO_IDS = ["bitcoin", "ethereum"]
MARKET_TICKERS = {
    "brent_oil": "BZ=F",
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
}

def extract_crypto_history(days: int):
    out = {"type": "crypto_history", "days": days, "timestamp": datetime.now(timezone.utc).isoformat(), "data": {}}
    for coin in CRYPTO_IDS:
        url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        out["data"][coin] = r.json()["prices"]  # list of [ms, price]
    return out

def extract_market_history(days: int):
    out = {"type": "market_history", "days": days, "timestamp": datetime.now(timezone.utc).isoformat(), "data": {}}
    for name, ticker in MARKET_TICKERS.items():
        df = yf.Ticker(ticker).history(period=f"{days}d", interval="1d")
        df = df.reset_index()
        # store list of {date, close}
        out["data"][name] = [{"date": str(row["Date"])[:10], "close": float(row["Close"])} for _, row in df.iterrows()]
    return out

def save(payload, prefix: str):
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    fname = RAW_PATH / f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Saved {prefix} history to {fname}")

if __name__ == "__main__":
    save(extract_crypto_history(DAYS), "crypto_hist")
    save(extract_market_history(DAYS), "market_hist")