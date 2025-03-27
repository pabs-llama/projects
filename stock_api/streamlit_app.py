import streamlit as st
from dotenv import load_dotenv
import os
import skl

st.title(":blue[Crypto] Historical Data")
# x = st.text_input ("Select your Crypto Currency")
# st.write(f"you selected {x}")
crypto_currency = st.selectbox(
    "Select your Cryptocurrency",
    ("Bitcoin (BTC)", "Ethereum (ETH)", "Tether (USDT)", "XRP (XRP)", "Binance Coin (BNB)"),
    index=None,
    placeholder="Select your Cryptocurrency"
)

st.header (f"{crypto_currency} data")
st.text ("blabla")
st.text ("more text")




