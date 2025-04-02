import os
import requests
from datetime import datetime

# best practice - break it into:
## Reusable logic functions (fetch_crypto_data)
## One top-level lambda_handler(event, context) that glues it all together

# Function to fetch multiple cryptos
def get_api_data(symbols=["BTC", "ETH", "USDT", "XRP", "SOL"], market="EUR"):
    api_key = os.environ["ALPHAVANTAGE_API_KEY"]
    all_data = []

    for symbol in symbols:
        url = (
            f"https://www.alphavantage.co/query"
            f"?function=DIGITAL_CURRENCY_DAILY&symbol={symbol}&market={market}&apikey={api_key}"
        )

        response = requests.get(url)
        data = response.json()

        if "Time Series (Digital Currency Daily)" not in data:
            print(f"❌ Skipping {symbol}, bad API response")
            continue

        ts = data["Time Series (Digital Currency Daily)"]
        latest_date = max(ts.keys())
        latest_data = ts[latest_date]

        all_data.append({
            "symbol": symbol,
            "date": latest_date,
            "open": float(latest_data["1. open"]),
            "high": float(latest_data["2. high"]),
            "low": float(latest_data["3. low"]),
            "close": float(latest_data["4. close"]),
            "volume": float(latest_data["5. volume"])
        })

    return all_data

# Lambda Handler (Think of lambda_handler as the “main” function Lambda runs when triggered)

# # test:
{
  "crypto_data": [
    {
      "symbol": "BTC",
      "date": "2025-03-28",
      "open": 68000.0,
      "high": 69000.0,
      "low": 67000.0,
      "close": 68500.0,
      "volume": 12345.0
    }
  ]
}



# correct package: 
# pip install --platform manylinux2014_x86_64 \
#   --target=. \
#   --implementation cp \
#   --python-version 3.12 \
#   --only-binary=:all: \
#   psycopg2-binary sqlalchemy

