import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()

def get_api_data():
    dbconn = os.getenv("DBCONN")
    engine = create_engine(dbconn)
  
    query = text("SELECT date, open, close, symbol FROM api_crypto_data")

    with engine.connect() as conn:
        df = pd.read_sql (query,conn)
    return df

api_data_df = get_api_data()

st.title(":blue[Crypto] Historical Data")

# crypto_currency = st.selectbox(
#     "Select your Cryptocurrency",
#     ("Bitcoin (BTC)", "Ethereum (ETH)", "Tether (USDT)", "XRP (XRP)", "SOLANA (SOL)"),
#     index=None,
#     placeholder="Select your Cryptocurrency"
# )

# pivoting table so each column will become a line, with date as index
pivot_df = api_data_df.pivot_table (
    index="date",
    columns="symbol", 
    values="close",
    aggfunc="last"
)

selected_cryptos = st.multiselect(
    "Select Cryptocurrency:",
    ["BTC", "ETH","USDT", "XRP","SOL"],#pivot_df.columns.tolist(),
    placeholder="Select your Cryptocurrency",
    # default="BTC"
)

st.header (f"{selected_cryptos[0]} data")
st.subheader(":blue[{selected_cryptos}] Historical Data")

if selected_cryptos:
    st.line_chart(pivot_df[selected_cryptos])






