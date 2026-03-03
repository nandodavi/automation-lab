import sqlite3
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Market Dashboard", layout="wide")
st.title("📈 Multi-Asset Market Dashboard")

DB_PATH = "data/market.db"
TABLE = "asset_prices"

# --- Auto refresh
st.sidebar.header("Settings")
auto = st.sidebar.toggle("Auto-refresh (60s)", value=True)
if auto:
    st_autorefresh(interval=60_000, key="refresh_60s")

@st.cache_data(ttl=30)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT asset, asset_type, price_usd, timestamp FROM {TABLE}", conn)
    conn.close()
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", utc=True)
    return df.sort_values("timestamp")

df = load_data()

if df.empty:
    st.warning("No data found yet. Run: extract -> transform -> load.")
    st.stop()

# --- Sidebar filters
types = ["All"] + sorted(df["asset_type"].unique().tolist())
selected_type = st.sidebar.selectbox("Asset type", types)

filtered = df.copy()
if selected_type != "All":
    filtered = filtered[filtered["asset_type"] == selected_type]

assets = sorted(filtered["asset"].unique().tolist())
default_assets = assets[:2] if len(assets) >= 2 else assets
selected_assets = st.sidebar.multiselect("Assets", assets, default=default_assets)

ma_windows = st.sidebar.multiselect("Moving averages (points)", [3, 5, 10, 20], default=[3, 5])

if not selected_assets:
    st.info("Select at least one asset.")
    st.stop()

filtered = filtered[filtered["asset"].isin(selected_assets)]

# --- Ensure enough points
counts = filtered.groupby("asset")["timestamp"].count().to_dict()

latest_ts = filtered["timestamp"].max()
st.caption(f"Last update (UTC): {latest_ts}")

# --- KPI cards
cols = st.columns(min(4, len(selected_assets)))
for i, asset in enumerate(selected_assets):
    a = filtered[filtered["asset"] == asset].sort_values("timestamp")
    last_price = a["price_usd"].iloc[-1]

    # percent change vs previous point
    if len(a) > 1:
        prev_price = a["price_usd"].iloc[-2]
        delta_pct = ((last_price - prev_price) / prev_price) * 100 if prev_price else 0.0
        delta_txt = f"{delta_pct:+.2f}%"
    else:
        delta_txt = "need 2+ pts"

    label = f"{asset.upper()} ({a['asset_type'].iloc[-1]})"
    cols[i % len(cols)].metric(label, f"{last_price:,.2f} USD", delta_txt)

st.divider()

# --- Build pivot for charts
pivot = (
    filtered.pivot_table(index="timestamp", columns="asset", values="price_usd", aggfunc="last")
    .sort_index()
)

# --- Price chart with moving averages
st.subheader("Price over time (with moving averages)")
price_df = pivot.copy()

# Add MA columns (one per asset per window)
for asset in selected_assets:
    if asset in price_df.columns:
        for w in ma_windows:
            price_df[f"{asset}_MA{w}"] = price_df[asset].rolling(window=w, min_periods=1).mean()

st.line_chart(price_df)

# --- Normalized performance chart (%)
st.subheader("Normalized performance (base = 100)")
norm = pivot.copy()

# Normalize each asset to 100 at its first available point
for col in norm.columns:
    first = norm[col].dropna()
    if not first.empty:
        base = first.iloc[0]
        norm[col] = (norm[col] / base) * 100

st.line_chart(norm)

st.divider()

# --- Quick data health panel
with st.expander("Data health / debug"):
    st.write("Points per asset:", counts)
    st.write("Latest rows:")
    st.dataframe(filtered.sort_values("timestamp").tail(20))