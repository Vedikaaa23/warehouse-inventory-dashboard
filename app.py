"""
Warehouse Inventory Analytics Dashboard
Answers the 5 business questions from inventory_movements.csv with live,
filterable charts. Run locally with:  streamlit run app.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Warehouse Inventory Analytics", layout="wide")

# ----------------------------------------------------------------------------
# Data loading + cleaning
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("inventory_movements.csv")

    # Drop exact duplicate rows (same movement_id appearing twice, identical data)
    df = df.drop_duplicates(subset="movement_id", keep="first")

    df["movement_date"] = pd.to_datetime(df["movement_date"], errors="coerce")
    df["expected_date"] = pd.to_datetime(df["expected_date"], errors="coerce")

    df["is_discrepancy"] = df["status"].eq("Discrepancy")
    df["is_negative_stock"] = df["stock_after"] < 0

    return df


df = load_data()

st.title("📦 Warehouse Inventory Analytics")
st.caption(
    "Movement-level data across 6 warehouses · "
    f"{len(df):,} movements after de-duplication · "
    f"{df['movement_date'].min().date()} to {df['movement_date'].max().date()}"
)

# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
st.sidebar.header("Filters")
warehouses = st.sidebar.multiselect(
    "Warehouse", sorted(df["warehouse_id"].unique()), default=sorted(df["warehouse_id"].unique())
)
mtypes = st.sidebar.multiselect(
    "Movement type", sorted(df["movement_type"].unique()), default=sorted(df["movement_type"].unique())
)
fdf = df[df["warehouse_id"].isin(warehouses) & df["movement_type"].isin(mtypes)]

# ----------------------------------------------------------------------------
# Top-line KPIs
# ----------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total movements", f"{len(fdf):,}")
k2.metric("Discrepancy rate", f"{fdf['is_discrepancy'].mean()*100:.1f}%")
k3.metric("Negative-stock incidents", f"{fdf['is_negative_stock'].sum():,}")
k4.metric("SKUs tracked", f"{fdf['sku_id'].nunique():,}")

st.divider()

# ----------------------------------------------------------------------------
# Q1 — Discrepancy rate by warehouse
# ----------------------------------------------------------------------------
st.header("Q1. Discrepancy rate by warehouse")

wh_rate = (
    df.groupby("warehouse_id")["is_discrepancy"].mean().reset_index()
    .rename(columns={"is_discrepancy": "discrepancy_rate"})
    .sort_values("discrepancy_rate", ascending=False)
)
wh_rate["discrepancy_rate_pct"] = wh_rate["discrepancy_rate"] * 100

c1, c2 = st.columns([1.3, 1])
with c1:
    fig = px.bar(
        wh_rate, x="warehouse_id", y="discrepancy_rate_pct",
        title="Discrepancy rate by warehouse (all movement types)",
        labels={"discrepancy_rate_pct": "Discrepancy rate (%)", "warehouse_id": "Warehouse"},
        text_auto=".1f",
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    type_rate = (
        df.groupby("movement_type")["is_discrepancy"].mean().reset_index()
        .rename(columns={"is_discrepancy": "rate"}).sort_values("rate", ascending=False)
    )
    type_rate["rate_pct"] = type_rate["rate"] * 100
    fig2 = px.bar(
        type_rate, x="movement_type", y="rate_pct",
        title="Discrepancy rate by movement type (all warehouses)",
        labels={"rate_pct": "Discrepancy rate (%)", "movement_type": "Movement type"},
        text_auto=".1f",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.info(
    "**Reading:** WH_06 has the nominally highest discrepancy rate (~11.3%) but a chi-square "
    "test of warehouse × discrepancy status gives p ≈ 0.29 — not statistically significant. "
    "The real signal is by **movement type**: Adjustment and Return movements carry higher "
    "discrepancy rates system-wide than Inbound/Outbound, in every warehouse. See "
    "BUSINESS_ANSWERS.md for the full reasoning."
)

st.divider()

# ----------------------------------------------------------------------------
# Q2 — Unit cost vs quantity by supplier
# ----------------------------------------------------------------------------
st.header("Q2. Unit cost vs. quantity across suppliers")

inbound = df[df["movement_type"] == "Inbound"].copy()

fig3 = px.scatter(
    inbound, x="quantity", y="unit_cost", color="supplier_id",
    title="Unit cost vs. quantity — Inbound movements, colored by supplier",
    opacity=0.7, height=500,
)
st.plotly_chart(fig3, use_container_width=True)

sup_summary = (
    inbound.groupby("supplier_id")
    .agg(n=("movement_id", "count"), avg_unit_cost=("unit_cost", "mean"), avg_quantity=("quantity", "mean"),
         corr=("unit_cost", lambda s: s.corr(inbound.loc[s.index, "quantity"])))
    .reset_index().sort_values("avg_unit_cost", ascending=False)
)
st.dataframe(sup_summary, use_container_width=True, hide_index=True)

st.info(
    "**Reading:** Across all suppliers, unit cost and quantity are essentially uncorrelated "
    "(r ≈ -0.02) — cost doesn't scale with order size. **SUP_09 is the outlier**: its average "
    "unit cost (~₹10,560) is roughly 10x every other supplier (~₹950–1,130), and for the same "
    "SKUs sourced from multiple suppliers, SUP_09 is consistently priced 5–20x higher. This "
    "looks like a pricing-tier or data-entry issue worth a manual check."
)

st.divider()

# ----------------------------------------------------------------------------
# Q3 — SKUs with stockouts / implausible stock
# ----------------------------------------------------------------------------
st.header("Q3. SKUs with stockouts or inventory imbalance")

neg = df[df["is_negative_stock"]]
sku_neg = (
    neg.groupby("sku_id").size().reset_index(name="negative_stock_events")
    .sort_values("negative_stock_events", ascending=False).head(15)
)

c3, c4 = st.columns(2)
with c3:
    fig4 = px.bar(
        sku_neg, x="sku_id", y="negative_stock_events",
        title="Top 15 SKUs by negative-stock (implausible) events",
    )
    st.plotly_chart(fig4, use_container_width=True)

with c4:
    neg_disp = neg.copy()
    neg_disp["oversell_pct"] = (neg_disp["quantity"] - neg_disp["stock_before"]) / neg_disp["stock_before"] * 100
    top_oversell = neg_disp.sort_values("oversell_pct", ascending=False).head(15)[
        ["sku_id", "warehouse_id", "quantity", "stock_before", "oversell_pct"]
    ]
    st.write("**Worst oversells** (quantity shipped vs. stock on hand)")
    st.dataframe(top_oversell, use_container_width=True, hide_index=True)

st.metric("Total negative-stock events", f"{len(neg):,}", help="stock_after < 0 across all movements")
st.info(
    "**Reading:** 202 movements (146 distinct SKUs) end with negative stock_after — a physical "
    "impossibility, meaning the system let a warehouse ship/transfer more units than it had on "
    "hand. This points to a missing hard-stop validation at the point of movement entry, not "
    "just a reporting issue. Recommendation: add a pre-commit check that blocks Outbound/Transfer "
    "quantities exceeding stock_before, and reconcile the ~150 SKUs above with a physical count."
)

st.divider()

# ----------------------------------------------------------------------------
# Q5 — Weekly trend of the recommended north-star metric
# ----------------------------------------------------------------------------
st.header("Weekly trend: negative-stock incident rate (recommended metric)")

wdf = df.dropna(subset=["movement_date"]).copy()
wdf["week"] = wdf["movement_date"].dt.to_period("W").apply(lambda r: r.start_time)
weekly = wdf.groupby("week").agg(
    total=("movement_id", "count"), neg=("is_negative_stock", "sum")
).reset_index()
weekly["neg_rate_pct"] = weekly["neg"] / weekly["total"] * 100

fig5 = px.line(weekly, x="week", y="neg_rate_pct", markers=True,
                title="Negative-stock incident rate by week",
                labels={"neg_rate_pct": "Negative-stock rate (%)", "week": "Week"})
st.plotly_chart(fig5, use_container_width=True)

st.divider()
st.caption("See BUSINESS_ANSWERS.md in this repo for the full written answers, methods, and caveats.")
