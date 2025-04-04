import os
import requests
from dateutil.parser import parse
import json

# 🧹 Clean + standardize date
def normalize_date(date_str):
    try:
        return parse(date_str).date().isoformat()
    except:
        return None

# 🔎 Fetch FT articles via SerpAPI using standard Google engine (sorted by date)
def fetch_ft_articles_from_serpapi(query, pages=1):
    api_key = os.environ["SERP_API_KEY"]
    all_results = []

    for page in range(pages):
        params = {
            "engine": "google",
            "q": f"{query} site:ft.com",
            "api_key": api_key,
            "tbs": "sbd:1",  # Sort by date
            "start": page * 10
        }

        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()

        for result in data.get("organic_results", []):
            article = {
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
                "date": normalize_date(result.get("date"))
            }
            if article["date"]:
                all_results.append(article)

    return all_results

# 🔁 Wrapper for all crypto
def scrape_ft_multi_crypto(crypto_queries, pages=1):
    print("🚀 Scraping Financial Times via SerpAPI...")
    all_articles = []

    for symbol, query in crypto_queries.items():
        print(f"🔍 Searching {symbol} ({query})")
        results = fetch_ft_articles_from_serpapi(query, pages=pages)
        for article in results:
            article["symbol"] = symbol
            all_articles.append(article)

    print(f"✅ Found {len(all_articles)} articles.")
    return all_articles


# 🧠 Lambda entry point
def lambda_handler(event, context):
    print("✅ Lambda triggered!")

    crypto_queries = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
        "XRP": "xrp",
        "SOL": "solana"
    }

    articles = scrape_ft_multi_crypto(crypto_queries, pages=1)

    return {
        "statusCode": 200,
        "ft_articles": articles
    }
