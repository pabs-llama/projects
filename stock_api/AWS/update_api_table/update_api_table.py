from sqlalchemy import create_engine, text
import os

def update_api_table(data):
    dbconn = os.environ["DBCONN"]
    engine = create_engine(dbconn)

    insert_sql = text("""
        INSERT INTO api_crypto_data (date, symbol, open, high, low, close, volume)
        VALUES (:date, :symbol, :open, :high, :low, :close, :volume)
        ON CONFLICT (date, symbol) DO NOTHING;
    """)

    with engine.begin() as conn:
        conn.execute(insert_sql, data)
        print(f"✅ Inserted {len(data)} rows (skipping any duplicates).")
