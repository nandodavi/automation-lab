import requests
import json
from datetime import datetime
from pathlib import Path

print("SCRIPT STARTED")

URL = "https://api.coingecko.com/api/v3/simple/price"

PARAMS = {
    "ids": "bitcoin,ethereum",
    "vs_currencies": "usd"
}

def extract_crypto_prices():
    print("Requesting data from API...")
    response = requests.get(URL, params=PARAMS)

    print("Status code:", response.status_code)

    data = response.json()
    print("Received data:", data)

    data["timestamp"] = datetime.utcnow().isoformat()

    return data


def save_raw_data(data):
    raw_path = Path("data/raw")
    raw_path.mkdir(parents=True, exist_ok=True)

    filename = raw_path / f"crypto_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Data saved to {filename}")


if __name__ == "__main__":
    try:
        crypto_data = extract_crypto_prices()
        save_raw_data(crypto_data)
    except Exception as e:
        print("ERROR OCCURRED:", e)