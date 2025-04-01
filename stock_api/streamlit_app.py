# Importing Libraries
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

#Load dotenv
load_dotenv()

# Fetching API data
def get_api_data():
    dbconn = st.secrets("DBCONN")
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
    dbconn = os.getenv("DBCONN")
    engine = create_engine(dbconn)
  
    query = text("SELECT title, link, snippet, date FROM ft_articles")

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
# ## Adding a Header to the chart
# st.subheader(f":blue[{', '.join(selected_cryptos)}] Historical Data")

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
price_color = "green" if change_pct > 0 else "red"
st.markdown(f"""
## :blue[{', '.join(selected_cryptos)}] Price Today: **{latest_price:.2f} EUR**  
<span style="color:{price_color}; font-size:18px">
{change_pct:+.2f}% over the last {time_range}
</span>
""", unsafe_allow_html=True)

# st.subheader(f":blue[{', '.join(selected_cryptos)}] Historical Data")

fig = go.Figure()

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

# Add closing price line
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["close"],
    mode="lines+markers",
    line=dict(color="green" if change_pct > 0 else "red"),
    name="Close Price"
))

max_point = df.loc[df["close"].idxmax()]
min_point = df.loc[df["close"].idxmin()]

# Max point
fig.add_trace(go.Scatter(
    x=[max_point["date"]],
    y=[max_point["close"]],
    mode="markers+text",
    marker=dict(color="green", size=10, symbol="triangle-up"),
    name="High",
    text=[f"High: {max_point['close']:.2f}"],
    textposition="top center"
))

# Min point
fig.add_trace(go.Scatter(
    x=[min_point["date"]],
    y=[min_point["close"]],
    mode="markers+text",
    marker=dict(color="red", size=10, symbol="triangle-down"),
    name="Low",
    text=[f"Low: {min_point['close']:.2f}"],
    textposition="bottom center"
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

st.plotly_chart(fig, use_container_width=True)

st.divider()

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
    colors = ["green" if x > 0 else "red" for x in change_df["change_pct"]]
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
            display_text= "Link"
            
        ),
    },
    hide_index=True,
    )


# def add_daily_change(df):
#     df = df.sort_values(["symbol", "date"])
#     df["change_pct"] = df.groupby("symbol")["close"].pct_change() * 100
#     df["change_pct"] = df["change_pct"].round(2)
#     return df

# df = add_daily_change(api_data_df)

# if selected_cryptos:
#     filtered_df = df[df["symbol"].isin(selected_cryptos)]

#     # Optional: Pivot for multi-line plot
#     pivot_pct = filtered_df.pivot(index="date", columns="symbol", values="change_pct")

#     st.subheader("📈 Daily % Change")
#     st.line_chart(pivot_pct)

# TOP MOVERS DF
# def top_movers_table(df):
#     latest_date = df["date"].max()
#     latest = df[df["date"] == latest_date].copy()
#     latest["change"] = latest["close"] - latest["open"]
#     latest["change_pct"] = (latest["change"] / latest["open"]) * 100
#     st.dataframe(latest[["symbol", "open", "close", "change", "change_pct"]].sort_values("change_pct", ascending=False))


# if selected_cryptos:
#     st.subheader("Top Movers")
#     for symbol in selected_cryptos:
#         top_movers_table(api_data_df)

# top movers bar chart (Shows which cryptos moved the most (up or down) on the latest day)

# def plot_top_movers(df):
#     df = df.sort_values(["symbol", "date"])
#     df["change_pct"] = df.groupby("symbol")["close"].pct_change() * 100

#     latest_date = df["date"].max()
#     latest = df[df["date"] == latest_date].copy()

#     latest["change_pct"] = latest["change_pct"].round(2)

#     st.subheader(f"📊 Top Movers on {latest_date.strftime('%Y-%m-%d')}")
#     st.bar_chart(latest.set_index("symbol")["change_pct"])

# plot_top_movers(api_data_df)

#  Volatility Shading (High - Low Area) Visualizes price range per day — like a daily volatility band.

# def plot_volatility_area(df, selected_symbols):
#     st.subheader("📉 Daily Volatility Range (High - Low)")

#     for symbol in selected_symbols:
#         symbol_df = df[df["symbol"] == symbol].copy().sort_values("date")
#         symbol_df["range"] = symbol_df["high"] - symbol_df["low"]

#         st.area_chart(symbol_df.set_index("date")["range"], height=200)
#         st.caption(f"{symbol} daily range in EUR")



# plot_volatility_area(api_data_df, selected_cryptos)

# import plotly.graph_objects as go

# def plot_colored_top_movers(df):
#     df = df.sort_values(["symbol", "date"])
#     df["change_pct"] = df.groupby("symbol")["close"].pct_change() * 100

#     latest_date = df["date"].max()
#     latest = df[df["date"] == latest_date].copy()
#     latest["change_pct"] = latest["change_pct"].round(2)

#     # Set color per row: green for gainers, red for losers
#     latest["color"] = latest["change_pct"].apply(lambda x: "blue" if x > 0 else "red")

#     fig = go.Figure()

#     fig.add_trace(go.Bar(
#         x=latest["symbol"],
#         y=latest["change_pct"],
#         marker_color=latest["color"],
#         text=latest["change_pct"].astype(str) + "%",
#         textposition="auto",
#     ))

#     fig.update_layout(
#         title=f"📊 Top Movers on {latest_date.strftime('%Y-%m-%d')}",
#         yaxis_title="Daily Change (%)",
#         xaxis_title="Cryptocurrency",
#         height=400
#     )
 
#     st.plotly_chart(fig, use_container_width=True)

# plot_colored_top_movers(api_data_df)

# Combine with FT articles to flag “news-driven” spikes
## GOAL: Highlight or flag days where a price spike coincides with article activity
### Step 1: Aggregate FT Articles by Date and Symbol

# def get_article_counts(df):
#     df["date"] = pd.to_datetime(df["date"])
#     article_counts = df.groupby(["date"]).size().reset_index(name="article_count")
#     return article_counts

# ### Step 2: Merge Article Counts with Crypto Data
# def merge_news_with_price(api_df, articles_df):
#     api_df["date"] = pd.to_datetime(api_df["date"])
#     articles_df["date"] = pd.to_datetime(articles_df["date"])

#     article_counts = get_article_counts(articles_df)

#     merged = pd.merge(api_df, article_counts, on="date", how="left")
#     merged["article_count"] = merged["article_count"].fillna(0).astype(int)

#     # Add daily % change
#     merged = merged.sort_values("date")
#     merged["change_pct"] = merged["close"].pct_change() * 100

#     return merged

# merged_df = merge_news_with_price(api_data_df, scrapping_data_df)

# ## Groupping by week and month

# # Convert date to datetime if not already
# merged_df["date"] = pd.to_datetime(merged_df["date"])

# # Grouping period column
# merged_df["week"] = merged_df["date"].dt.to_period("W")  # weekly
# merged_df["month"] = merged_df["date"].dt.to_period("M")  # or monthly

# # Aggregate article count and avg % change by week
# weekly_summary = merged_df.groupby(["week"]).agg({
#     "article_count": "sum",
#     "change_pct": "mean"  # or std for volatility
# }).reset_index()

# selected = st.selectbox("Choose view:", ["weekly", "monthly"])
# group_col = "week" if selected == "weekly" else "month"

# summary_df = merged_df.copy()
# # summary_df[group_col] = summary_df["date"].dt.to_period("W" if selected == "weekly" else "M")
# summary_df["week"] = summary_df["date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%Y-%m-%d"))

# agg_df = summary_df.groupby(["symbol", group_col]).agg({
#     "article_count": "sum",
#     "change_pct": "mean"
# }).reset_index()

# for symbol in selected_cryptos:
#     symbol_df = agg_df[agg_df["symbol"] == symbol]
#     st.subheader(f"{symbol} — Avg Change vs Article Count ({selected})")

#     st.bar_chart(
#         symbol_df.set_index(group_col)[["change_pct", "article_count"]],
#         height=300
#     )


# ### Flag "News-Driven Spikes"
# # Define spike = abs(daily change > 5%) and at least 1 article that day
# news_spikes = merged_df[
#     (merged_df["article_count"] > 0) & 
#     (merged_df["change_pct"].abs() > 5)
# ]

# st.subheader("📰 Price Spikes with FT Article Coverage")
# st.dataframe(news_spikes[["date", "change_pct", "article_count"]])
# st.subheader("📰 News-Driven Price Spikes")


# st.scatter_chart(news_spikes[["article_count", "change_pct"]])


# import plotly.graph_objects as go

# def plot_dual_axis_news_vs_price(df, symbol, time_col="week"):
#     df = df[df["symbol"] == symbol].copy()
    
#     # Ensure sorting
#     df = df.sort_values(time_col)

#     # Build figure
#     fig = go.Figure()

#     # Bar: article count (left y-axis)
#     fig.add_trace(go.Bar(
#         x=df[time_col],
#         y=df["article_count"],
#         name="Article Count",
#         marker_color='rgba(0, 102, 204, 0.6)',
#         yaxis="y1"
#     ))

#     # Line: % change (right y-axis)
#     fig.add_trace(go.Scatter(
#         x=df[time_col],
#         y=df["change_pct"],
#         name="Avg % Change",
#         mode="lines+markers",
#         marker=dict(color="crimson"),
#         yaxis="y2"
#     ))

#     fig.update_layout(
#     title=f"{symbol} — Avg % Change vs Article Volume ({time_col})",
#     xaxis=dict(title="Date"),
#     yaxis=dict(
#         title="Article Count",
#         side="left",
#         showgrid=False
#     ),
#     yaxis2=dict(
#         title="% Change",
#         overlaying="y",
#         side="right",
#         showgrid=False,
#         tickformat=".2f",  # ✅ Format as float, not millions
#         rangemode="tozero"
#     ),
#     legend=dict(x=0.01, y=0.99),
#     height=400
# )
#     st.plotly_chart(fig, use_container_width=True)

# merged_df["week"] = merged_df["date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%Y-%m-%d"))

# weekly_summary = merged_df.groupby(["symbol", "week"]).agg({
#     "article_count": "sum",
#     "change_pct": "mean"
# }).reset_index()

# for symbol in selected_cryptos:
#     plot_dual_axis_news_vs_price(weekly_summary, symbol, time_col="week")




# Dinamy time based top movers chart

# Add Time Period Toggle


