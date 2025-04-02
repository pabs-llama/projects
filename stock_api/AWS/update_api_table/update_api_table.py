import os
from sqlalchemy import create_engine, text

def insert_crypto_data_to_db(data):
    dbconn = os.environ["DBCONN"]
    engine = create_engine(dbconn)

    insert_sql = text("""
        INSERT INTO api_crypto_data (date, symbol, open, high, low, close, volume)
        VALUES (:date, :symbol, :open, :high, :low, :close, :volume)
        ON CONFLICT (date, symbol) DO NOTHING;
    """)

    with engine.begin() as conn:
        conn.execute(insert_sql, data)
        print(f"✅ Inserted {len(data)} rows (skipping duplicates).")

# Lambda entry point
def lambda_handler(event, context):
    # Lambda will pass `event` from previous function or test
    data = event.get("crypto_data")

    if not data:
        return {
            "statusCode": 400,
            "body": "❌ No crypto_data provided in event"
        }

    insert_crypto_data_to_db(data)

    return {
        "statusCode": 200,
        "body": f"✅ Inserted {len(data)} rows into DB"
    }
