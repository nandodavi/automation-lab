import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np

DB = Path("data/market.db")
TABLE_DAILY = "asset_daily"

st.set_page_config(page_title="Market Dashboard", layout="wide")

@st.cache_data(ttl=60)
def get_date_bounds():
    with sqlite3.connect(DB) as conn:
        row = conn.execute(
            f"SELECT MIN(date), MAX(date), COUNT(*) FROM {TABLE_DAILY}"
        ).fetchone()
    min_date, max_date, count_rows = row
    if min_date is None or max_date is None:
        return None, None, 0
    return pd.to_datetime(min_date).date(), pd.to_datetime(max_date).date(), int(count_rows)

@st.cache_data(ttl=60)
def load_daily(start_date, end_date, assets=None, asset_types=None):
    params = {"start": str(start_date), "end": str(end_date)}
    where = ["date >= :start", "date <= :end"]

    if assets:
        placeholders = ", ".join([f":a{i}" for i in range(len(assets))])
        where.append(f"asset IN ({placeholders})")
        for i, a in enumerate(assets):
            params[f"a{i}"] = a

    if asset_types:
        placeholders = ", ".join([f":t{i}" for i in range(len(asset_types))])
        where.append(f"asset_type IN ({placeholders})")
        for i, t in enumerate(asset_types):
            params[f"t{i}"] = t

    sql = f"""
        SELECT date, asset, asset_type, price_usd
        FROM {TABLE_DAILY}
        WHERE {" AND ".join(where)}
        ORDER BY asset, date
    """

    with sqlite3.connect(DB) as conn:
        df = pd.read_sql_query(sql, conn, params=params)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
    df = df.dropna(subset=["price_usd"])
    return df

@st.cache_data(ttl=60)
def list_assets_and_types():
    with sqlite3.connect(DB) as conn:
        assets = pd.read_sql_query(
            f"SELECT DISTINCT asset FROM {TABLE_DAILY} ORDER BY asset", conn
        )["asset"].tolist()
        types_ = pd.read_sql_query(
            f"SELECT DISTINCT asset_type FROM {TABLE_DAILY} ORDER BY asset_type", conn
        )["asset_type"].tolist()
    return assets, types_

def add_metrics(df):
    # daily returns + normalized performance (base 100)
    df = df.sort_values(["asset", "date"]).copy()
    df["daily_return"] = df.groupby("asset")["price_usd"].pct_change()

    base = df.groupby("asset")["price_usd"].transform("first")
    df["normalized_100"] = (df["price_usd"] / base) * 100.0
    return df

# ---------------- UI ----------------
st.title("📈 Market Dashboard (Histórico)")

if not DB.exists():
    st.error(f"Banco não encontrado em: {DB}")
    st.stop()

min_d, max_d, nrows = get_date_bounds()
if not min_d:
    st.error("Não encontrei dados em asset_daily. Rode o loader.")
    st.stop()

st.caption(f"Dados disponíveis: **{min_d} → {max_d}** | Linhas: **{nrows}**")

assets_all, types_all = list_assets_and_types()

with st.sidebar:
    st.header("Filtros")
    mode = st.radio("Modo", ["Histórico"], index=0)

    date_range = st.date_input(
        "Intervalo de datas",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
    )
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date, end_date = min_d, max_d

    sel_types = st.multiselect("Tipos", options=types_all, default=types_all)
    sel_assets = st.multiselect("Ativos", options=assets_all, default=assets_all)

df = load_daily(start_date, end_date, assets=sel_assets, asset_types=sel_types)

if df.empty:
    st.warning("Sem dados para esse filtro. Tente ampliar o intervalo ou selecionar outros ativos.")
    st.stop()

df = add_metrics(df)

# ---------------- Correlation & Volatility ----------------

# Pivot returns
returns_df = (
    df.dropna(subset=["daily_return"])
      .pivot(index="date", columns="asset", values="daily_return")
)

# Correlation matrix
corr_matrix = returns_df.corr()

# Volatility (annualized)
volatility = returns_df.std() * np.sqrt(252)
volatility_df = volatility.reset_index()
volatility_df.columns = ["asset", "annualized_volatility"]

# ---------------- Layout ----------------
c1, c2, c3 = st.columns(3)
c1.metric("Período (dias)", (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1)
c2.metric("Ativos", df["asset"].nunique())
c3.metric("Observações", len(df))

st.divider()

left, right = st.columns([2, 1])

with left:
    st.subheader("Performance normalizada (base 100)")
    fig_norm = px.line(
        df,
        x="date",
        y="normalized_100",
        color="asset",
        markers=False,
        hover_data={"asset_type": True, "price_usd": ":.2f", "normalized_100": ":.2f"},
    )
    fig_norm.update_layout(legend_title_text="Ativo", yaxis_title="Base 100")
    st.plotly_chart(fig_norm, use_container_width=True)

    st.subheader("Preço (USD)")
    fig_price = px.line(
        df,
        x="date",
        y="price_usd",
        color="asset",
        markers=False,
        hover_data={"asset_type": True, "price_usd": ":.2f"},
    )
    fig_price.update_layout(legend_title_text="Ativo", yaxis_title="USD")
    st.plotly_chart(fig_price, use_container_width=True)

with right:
    st.subheader("Retorno diário (%)")
    df_ret = df.dropna(subset=["daily_return"]).copy()
    df_ret["daily_return_pct"] = df_ret["daily_return"] * 100.0

    fig_ret = px.bar(
        df_ret,
        x="date",
        y="daily_return_pct",
        color="asset",
        barmode="group",
        hover_data={"asset_type": True, "daily_return_pct": ":.2f"},
    )
    fig_ret.update_layout(yaxis_title="%")
    st.plotly_chart(fig_ret, use_container_width=True)

    st.subheader("Tabela")
    show_cols = ["date", "asset", "asset_type", "price_usd", "daily_return", "normalized_100"]
    st.dataframe(
        df[show_cols].sort_values(["date", "asset"], ascending=[False, True]),
        use_container_width=True,
        height=420,
    )
st.divider()
st.header("📊 Risk & Correlation Analysis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Correlation Heatmap (Daily Returns)")
    fig_corr = px.imshow(
        corr_matrix,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
    )
    st.plotly_chart(fig_corr, use_container_width=True)

with col2:
    st.subheader("Annualized Volatility")
    fig_vol = px.bar(
        volatility_df,
        x="asset",
        y="annualized_volatility",
        text="annualized_volatility",
    )
    fig_vol.update_traces(texttemplate="%.2f", textposition="outside")
    fig_vol.update_layout(yaxis_title="Volatility (Annualized)")
    st.plotly_chart(fig_vol, use_container_width=True)      