import os
import requests
import psycopg2

# Hugging Face API
HF_API_KEY = os.environ["HF_API_KEY"]
HF_MODEL_URL = "https://api-inference.huggingface.co/models/mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# PostgreSQL connection (Railway)
DBCONN = os.environ["DBCONN"]

# Get sentiment and score
def get_sentiment(snippet):
    if not snippet:
        return ("unknown", None)
    try:
        response = requests.post(HF_MODEL_URL, headers=HEADERS, json={"inputs": snippet})
        result = response.json()
        if isinstance(result, list) and result:
            label = result[0][0]['label'].lower()
            score_map = {"positive": 1, "neutral": 0, "negative": -1}
            return label, score_map.get(label, None)
    except Exception as e:
        print(f"Sentiment error: {e}")
    return ("error", None)

# Lambda handler
def lambda_handler(event, context):
    print("✅ Sentiment Lambda triggered!")

    try:
        conn = psycopg2.connect(DBCONN)
        cur = conn.cursor()

        # 1. Fetch articles missing sentiment
        cur.execute("""
            SELECT link, snippet FROM ft_all_crypto_articles
            WHERE sentiment IS NULL OR sentiment_score IS NULL
            LIMIT 50;
        """)
        articles = cur.fetchall()

        if not articles:
            print("No articles to process.")
            return {"statusCode": 200, "body": "No articles to update."}

        print(f"🧠 Processing {len(articles)} articles...")

        # 2. Analyze and update
        for link, snippet in articles:
            sentiment, score = get_sentiment(snippet)
            cur.execute("""
                UPDATE ft_all_crypto_articles
                SET sentiment = %s, sentiment_score = %s
                WHERE link = %s;
            """, (sentiment, score, link))

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Sentiment update complete.")

        return {
            "statusCode": 200,
            "body": f"Updated sentiment for {len(articles)} articles."
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"statusCode": 500, "body": str(e)}
