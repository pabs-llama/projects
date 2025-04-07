import os
import json
from sqlalchemy import create_engine, text

# ✅ Insert into Railway
def insert_ft_articles_to_db(articles):
    dbconn = os.environ["DBCONN"]
    engine = create_engine(dbconn)

    insert_sql = text("""
        INSERT INTO ft_articles (title, link, snippet, date, symbol)
        VALUES (:title, :link, :snippet, :date, :symbol)
        ON CONFLICT (link) DO NOTHING;
    """)

    with engine.begin() as conn:
        conn.execute(insert_sql, articles)
        print(f"✅ Inserted {len(articles)} articles.")

# 🧠 Lambda entry point
def lambda_handler(event, context):
    print("✅ Lambda triggered!")
    print("📦 Event Payload:\n", json.dumps(event, indent=2))

    # Extract data from previous Lambda
    articles = event.get("responsePayload", {}).get("ft_articles", [])

    if not articles:
        print("❌ No ft_articles found in event.")
        return {
            "statusCode": 400,
            "body": "No ft_articles provided."
        }

    insert_ft_articles_to_db(articles)

    return {
        "statusCode": 200,
        "body": f"✅ Inserted {len(articles)} articles."
    }
