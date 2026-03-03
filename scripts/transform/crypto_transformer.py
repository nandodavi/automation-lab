import json
import pandas as pd
from pathlib import Path

print("TRANSFORM STARTED")

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")


def get_latest_raw_file():
    files = list(RAW_PATH.glob("crypto_*.json"))
    if not files:
        raise FileNotFoundError("No raw crypto files found.")
    
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file


def transform_crypto_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    timestamp = data.pop("timestamp")

    records = []
    for coin, values in data.items():
        records.append({
            "coin": coin,
            "price_usd": values["usd"],
            "timestamp": timestamp
        })

    df = pd.DataFrame(records)
    return df


def save_processed_data(df):
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_PATH / "crypto_prices.csv"

    if output_file.exists():
        df.to_csv(output_file, mode="a", header=False, index=False)
    else:
        df.to_csv(output_file, index=False)

    print(f"Processed data saved to {output_file}")


if __name__ == "__main__":
    try:
        latest_file = get_latest_raw_file()
        print(f"Latest raw file: {latest_file}")

        df = transform_crypto_data(latest_file)
        print(df)

        save_processed_data(df)

    except Exception as e:
        print("ERROR:", e)