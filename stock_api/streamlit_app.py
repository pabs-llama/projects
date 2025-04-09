# Importing Libraries
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import datetime
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

#Load dotenv
load_dotenv()

# Fetching API data
def get_api_data():
    dbconn = st.secrets["DBCONN"]
    engine = create_engine(dbconn)
  
    query = text("SELECT date, open, close, high, low, volume, symbol FROM api_crypto_data")

    with engine.connect() as conn:
        df = pd.read_sql (query,conn)
    return df

api_data_df = get_api_data()

# Round all float columns to 2 decimals
api_data_df = api_data_df.round(2)

# Fetching Scrapping data
def get_scrapping_data():
    dbconn = st.secrets["DBCONN"]
    engine = create_engine(dbconn)
  
    query = text("SELECT title, link, snippet, date, symbol, sentiment,sentiment_score " \
    "FROM ft_all_crypto_articles ORDER BY date DESC")

    with engine.connect() as conn:
        df = pd.read_sql (query,conn)
    return df

scrapping_data_df = get_scrapping_data()

# Adding Title

st.title("Crypto Analysis")

# Creating a Line chart for each crypto
## filtering
api_data_filtered_df = api_data_df[["date","symbol","open","close"]]
##  pivoting table so each column will become a line, with date as index
pivot_df = api_data_df.pivot_table (
    index="date",
    columns="symbol", 
    values="close",
    aggfunc="last"
)

## Creating a multiselect box so user can choose between crytps
selected_cryptos = st.pills(
    "Select Cryptocurrency:",
    ["BTC", "ETH","USDT", "XRP","SOL"],#pivot_df.columns.tolist(),
    # placeholder="Select your Cryptocurrency",
    selection_mode= "multi",
    default="BTC"
)

# interactive line graph

from datetime import datetime, timedelta

## Time filter dropdown
time_range = st.selectbox("Select Time Range", ["1W","1M", "3M", "6M", "YTD", "1Y"])

## Convert to days
days_map = {
    "1W": 7,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "YTD": (datetime.now() - datetime(datetime.now().year, 1, 1)).days,
    "1Y": 365
}
days = days_map[time_range]
cutoff_date = datetime.now() - timedelta(days=days)

## filter data
symbol = selected_cryptos[0]  # or use a selectbox for single symbol
df = api_data_df[api_data_df["symbol"] == symbol].copy()
df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] >= cutoff_date]
df = df.sort_values("date")

# Optional: Resample to weekly for smoother lines if range is big
if time_range in ["3M", "6M", "YTD", "1Y"]:
    df = df.set_index("date").resample("W").last().reset_index()

## Get Current Price & % Change
latest_price = df["close"].iloc[-1]
initial_price = df["close"].iloc[0]
change_pct = ((latest_price - initial_price) / initial_price) * 100

## Show Price + Change in Header
price_color = "cyan" if change_pct > 0 else "magenta"
st.markdown(f"""
## :blue[{', '.join(selected_cryptos)}] Price Today: **{latest_price:.2f} EUR**  
<span style="color:{price_color}; font-size:18px">
{change_pct:+.2f}% over the last {time_range}</span>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 5px'></div>", unsafe_allow_html=True) # adding space 

# st.subheader(f":blue[{', '.join(selected_cryptos)}] Historical Data")

fig = go.Figure()

# Add closing price line
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["close"],
    mode="lines+markers",
    line=dict(color="cyan" if change_pct > 0 else "magenta"),
    name="Close Price"
))

max_point = df.loc[df["close"].idxmax()]
min_point = df.loc[df["close"].idxmin()]

# Max point
fig.add_trace(go.Scatter(
    x=[max_point["date"]],
    y=[max_point["close"]],
    mode="markers+text",
    marker=dict(color="cyan", size=10, symbol="triangle-up"),
    name="High",
    text=[f"High: {max_point['close']:.2f}"],
    textposition="top center"
))

# Min point
fig.add_trace(go.Scatter(
    x=[min_point["date"]],
    y=[min_point["close"]],
    mode="markers+text",
    marker=dict(color="magenta", size=10, symbol="triangle-down"),
    name="Low",
    text=[f"Low: {min_point['close']:.2f}"],
    textposition="bottom center"
))

#add toggle
show_volume = st.toggle("Show Volume", value=True)
if show_volume:
    fig.add_trace(go.Bar(
        x=df["date"],
        y=df["volume"],
        name="Volume",
        marker=dict(color="lightblue", opacity=0.3),
        yaxis="y2"
    ))

fig.update_layout(
    # title=f"{symbol} Closing Price ({time_range})",
    xaxis_title="Date",
    yaxis=dict(title="Closing Price (EUR)"),
    yaxis2=dict(
        title="Volume",
        overlaying="y",
        side="right",
        showgrid=False,
        rangemode="tozero"
    ),
    hovermode="x unified",
    height=450,
    legend=dict(
        x=0.85, 
        y=0.99,
        # xanchor = "right",
        # yanchor = "top",
        bgcolor="rgba(0,0,0,0)",  # ✅ transparent background
        bordercolor="rgba(0,0,0,0)",)  # ✅ no border)
)

st.plotly_chart(fig)


st.divider()

# TOP MOVERS
st.subheader(f"📊 Top Movers")

change_period = st.selectbox("Select Timeframe for Top Movers", ["1Y", "6M", "1M","1W","1D"])

# Map to timedelta
period_days_map = {
    "1D": 1,
    "1W": 7,
    "1M": 30,
    "6M": 180,
    "1Y": 365
}
delta = timedelta(days=period_days_map[change_period])
cutoff = datetime.now() - delta

# % Change line chart

# Calculate % Change Per Symbol
def calculate_top_movers(df, cutoff_date):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= cutoff_date]
    df = df.sort_values(["symbol", "date"])

    # Get first and last price in period for each symbol
    first_prices = df.groupby("symbol").first()["close"]
    last_prices = df.groupby("symbol").last()["close"]

    change_pct = ((last_prices - first_prices) / first_prices * 100).round(2)
    change_df = change_pct.reset_index(name="change_pct").sort_values("change_pct", ascending=False)
    return change_df

# Plot with Plotly Colored Bars
def plot_top_movers(change_df, label):
    colors = ["cyan" if x > 0 else "magenta" for x in change_df["change_pct"]]
    fig = go.Figure(go.Bar(
        x=change_df["symbol"],
        y=change_df["change_pct"],
        marker_color=colors,
        text=change_df["change_pct"].astype(str) + "%",
        textposition="auto"
    ))


    fig.update_layout(
        xaxis_title="Cryptocurrency",
        yaxis_title="% Change",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

change_df = calculate_top_movers(api_data_df, cutoff)
plot_top_movers(change_df, change_period)

st.divider()

import plotly.graph_objects as go

# def candlestick_chart(df, symbol):
#     df = df[df["symbol"] == symbol].sort_values("date")
#     fig = go.Figure(data=[go.Candlestick(
#         x=df["date"],
#         open=df["open"],
#         high=df["high"],
#         low=df["low"],
#         close=df["close"]
#     )])
#     fig.update_layout(title=f"{symbol} Price Movement", xaxis_title="Date", yaxis_title="Price (EUR)")
#     st.plotly_chart(fig, use_container_width=True)


# # 👉 Loop through selected cryptos to show multiple candlestick charts
# if selected_cryptos:
#     st.subheader("Candlestick Charts")
#     for symbol in selected_cryptos:
#         candlestick_chart(api_data_df, symbol)

# Daily Change % Line
st.subheader(f"📈 % Change")
change_freq = st.radio(
    "Select % Change Interval",
    ["Daily", "Weekly", "Monthly"],
    horizontal=True
)

def calculate_change(df, freq="Daily"):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["symbol", "date"])

    if freq == "Daily":
        df["change_pct"] = df.groupby("symbol")["close"].pct_change() * 100

    else:
        # Resample to weekly or monthly, take the last closing price in each period
        rule = {"Weekly": "W", "Monthly": "M"}[freq]
        df = df.set_index("date")
        df = df.groupby("symbol").resample(rule)["close"].last().reset_index()

        # Now calculate % change across the new intervals
        df["change_pct"] = df.groupby("symbol")["close"].pct_change() * 100

    df["change_pct"] = df["change_pct"].round(2)
    return df

change_df = calculate_change(api_data_df, freq=change_freq)

if selected_cryptos:
    filtered_df = change_df[change_df["symbol"].isin(selected_cryptos)]
    pivot_pct = filtered_df.pivot(index="date", columns="symbol", values="change_pct")
    st.line_chart(pivot_pct)

# Displaying a dataframe with the scraped data

st.subheader(f":blue[{', '.join(selected_cryptos)}] Financial Times Articles")

# 1. Convert date column to datetime (if not already)
scrapping_data_df["date"] = pd.to_datetime(scrapping_data_df["date"])

# # 2. Crypto selection
# selected_cryptos_2 = st.pills(
#     "Select Symbol:",
#     ["BTC", "ETH", "USDT", "XRP", "SOL"],
#     selection_mode="multi",
#     default="BTC"
# )

# 3. Date range selection
min_date = scrapping_data_df["date"].min().date()
max_date = scrapping_data_df["date"].max().date()

start_date, end_date = st.date_input(
    "Select date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# ✅ Convert to datetime for filtering
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# 4. Filter by crypto + date range
filtered_df = scrapping_data_df[
    (scrapping_data_df["symbol"].isin(selected_cryptos)) &
    (scrapping_data_df["date"].between(start_date, end_date))
]

# 5. Display filtered data
st.data_editor(
    filtered_df,
    column_config={
        "title": "Title",
        "snippet": "Snippet",
        "date": "Date",
        "link": st.column_config.LinkColumn(
            "Link", 
            help="Check the article",
            validate=r"^https://www\.ft\.com/.*",
            max_chars=100,
            display_text="Link"
        ),
    },
    hide_index=True,
)

#sentiment analysis line chart

scrapping_data_df['date'] = pd.to_datetime(scrapping_data_df['date'])

# -- Main Title
st.subheader("📈 Crypto Sentiment Trends")

# -- Controls: multi-select for multiple cryptos
available_cryptos = scrapping_data_df['symbol'].unique().tolist()
selected_cryptos = st.multiselect("Select cryptocurrencies", available_cryptos, default=available_cryptos[:1])

time_granularity = st.selectbox("Select time period", ['Daily', 'Weekly', 'Monthly', 'Yearly'])

# -- Date filter
filtered_df = scrapping_data_df[
    (scrapping_data_df['symbol'].isin(selected_cryptos)) &
    (scrapping_data_df['date'] >= pd.to_datetime("2024-09-01"))
]

# -- Resample frequency
resample_rule = {
    'Daily': 'D',
    'Weekly': 'W',
    'Monthly': 'M',
    'Yearly': 'Y'
}[time_granularity]

# -- Group + resample by symbol and date
sentiment_trend = (
    filtered_df
    .set_index('date')
    .groupby('symbol')['sentiment_score']
    .resample(resample_rule)
    .mean()
    .reset_index()
)

# -- Plotly line chart with color per symbol
fig = px.line(
    sentiment_trend,
    x='date',
    y='sentiment_score',
    color='symbol',
    markers=True,
    title=f"Sentiment Trend Over Time ({time_granularity})",
    labels={'sentiment_score': 'Avg Sentiment Score', 'date': 'Date', 'symbol': 'Crypto'},
)

fig.update_layout(
    template='plotly_dark',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    font=dict(color='white'),
)

st.plotly_chart(fig, use_container_width=True)



