import yfinance as yf
import json
from datetime import datetime, timezone
from pathlib import Path

print("MARKET EXTRACTION STARTED")

TICKERS = {
    "brent_oil": "BZ=F",
    "sp500": "^GSPC",
    "nasdaq": "^IXIC"
}

RAW_PATH = Path("data/raw")


def extract_market_data():
    data = {}
    
    for name, ticker in TICKERS.items():
        asset = yf.Ticker(ticker)
        price = asset.history(period="1d")["Close"].iloc[-1]
        
        data[name] = {"usd": float(price)}

    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    return data


def save_raw_data(data):
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    filename = RAW_PATH / f"market_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
        
    print(f"Market data saved to {filename}")


if __name__ == "__main__":
    market_data = extract_market_data()
    save_raw_data(market_data)