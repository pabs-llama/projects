# Importing Libraries
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

#Load dotenv
load_dotenv()

# Fetching API data
def get_api_data():
    dbconn = os.getenv("DBCONN")
    engine = create_engine(dbconn)
  
    query = text("SELECT date, open, close, symbol FROM api_crypto_data")

    with engine.connect() as conn:
        df = pd.read_sql (query,conn)
    return df

api_data_df = get_api_data()

# Fetching Scrapping data
def get_scrapping_data():
    dbconn = os.getenv("DBCONN")
    engine = create_engine(dbconn)
  
    query = text("SELECT title, link, snippet, date FROM ft_articles")

    with engine.connect() as conn:
        df = pd.read_sql (query,conn)
    return df

scrapping_data_df = get_scrapping_data()

# Adding Title

st.title(":blue[Crypto] Historical Data")

# crypto_currency = st.selectbox(
#     "Select your Cryptocurrency",
#     ("Bitcoin (BTC)", "Ethereum (ETH)", "Tether (USDT)", "XRP (XRP)", "SOLANA (SOL)"),
#     index=None,
#     placeholder="Select your Cryptocurrency"
# )

# Creating a Line chart for each crypto
##  pivoting table so each column will become a line, with date as index
pivot_df = api_data_df.pivot_table (
    index="date",
    columns="symbol", 
    values="close",
    aggfunc="last"
)

## Creating a multiselect box so user can choose between crytps
selected_cryptos = st.multiselect(
    "Select Cryptocurrency:",
    ["BTC", "ETH","USDT", "XRP","SOL"],#pivot_df.columns.tolist(),
    placeholder="Select your Cryptocurrency",
    default="BTC"
)
## Adding a Header to the chart
st.header (f"{selected_cryptos[0]} data")
st.subheader(":blue[{selected_cryptos}] Historical Data")

## Plotting the linechart
if selected_cryptos:
    st.line_chart(pivot_df[selected_cryptos])

# Displaying a dataframe with the scraped data

st.data_editor(
    scrapping_data_df,
    column_config={
        "title":"Title",
        "snippet":"Snippet",
        "date":"Date",
        "link": st.column_config.LinkColumn(
            "Link", 
            help= "Check the article",
            validate = r"^https://[a-z]+\.streamlit\.app$",
            max_chars=100,
            display_text= "link"
        ),
    },
    hide_index=True,
    )

