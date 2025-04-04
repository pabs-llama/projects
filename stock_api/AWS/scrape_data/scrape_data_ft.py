# 🔹 Step 1: scrape_data.py — Scrape today’s news
## Only grab 1 page per crypto (to reduce load time)
## Only return articles from today
## Return JSON data (ready to send to the insert Lambda)

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def scrape_ft_today(queries, pages=1):
    base_url = "https://www.ft.com/search"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "DNT": "1",  # Do Not Track header
    "Upgrade-Insecure-Requests": "1",
}

    today_str = datetime.now().strftime("%Y-%m-%d")
    all_results = []

    for symbol, query in queries.items():
        print(f"🔍 Searching for {symbol} ({query})")

        for page in range(1, pages + 1):
            params = {
                "q": query,
                "sort": "date",
                "isFirstView": "true",
                "page": page
            }

            response = requests.get(base_url, headers=headers, params=params)
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("li", class_="search-results__list-item")

            for item in items:
                title_tag = item.find("a", class_="js-teaser-heading-link")
                snippet_tag = item.find("a", class_="js-teaser-standfirst-link")
                date_tag = item.find("time", class_="o-teaser__timestamp-date")

                # if not date_tag or date_tag.get("datetime")[:10] != today_str:
                #     continue  # Skip non-today articles

                title = title_tag.get_text(strip=True) if title_tag else None
                link = "https://www.ft.com" + title_tag["href"] if title_tag else None
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else None

                # ---- Date Handling ----
                raw_date = None
                date = None

                if date_tag:
                    if "datetime" in date_tag.attrs:
                        raw_date = date_tag["datetime"]
                    else:
                        raw_date = date_tag.get_text(strip=True)

                if raw_date:
                    try:
                        date = datetime.fromisoformat(raw_date).strftime("%Y-%m-%d")
                    except:
                        try:
                            date = datetime.strptime(raw_date, "%B %d, %Y").strftime("%Y-%m-%d")
                        except Exception as e:
                            print(f"❌ Could not parse date: {raw_date} — {e}")
                
                #optional: only todays articles
                if date != today_str:
                    continue

                
                all_results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "date": today_str,
                    "symbol": symbol
                })

            time.sleep(1)

    return all_results


# Lambda handler
def lambda_handler(event, context):
    crypto_queries = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
        "XRP": "xrp",
        "SOL": "solana"
    }

    print("🚀 Scraping Financial Times for today’s crypto articles...")
    results = scrape_ft_today(crypto_queries)

    print(f"✅ Found {len(results)} articles")
    return {
        "statusCode": 200,
        "ft_articles": results
    }
