#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Netflix | Viewing Insights",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)

RED = "#E50914"
INK = "#141414"
MUTED = "#737373"
PALETTE = [RED, "#262626", "#6B6B6B", "#A8A8A8", "#D5D5D5", "#8F1018", "#4A4A4A", "#B83B42"]

st.markdown(
    """
    <style>
    :root { --netflix-red: #E50914; --netflix-ink: #141414; }
    .stApp { background: #f5f5f5; color: var(--netflix-ink); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #141414; }
    [data-testid="stSidebar"] * { color: #f5f5f5; }
    [data-testid="stSidebar"] [data-baseweb="select"] div { color: #141414; }
    .dashboard-head {
        background: #141414; color: #fff; padding: 1.35rem 1.6rem;
        border-top: 5px solid #E50914; margin: 0 0 1.35rem;
    }
    .dashboard-kicker { color: #E50914; font-size: .72rem; font-weight: 800;
        letter-spacing: .12em; text-transform: uppercase; margin-bottom: .35rem; }
    .dashboard-title { color: #fff; font-size: 1.8rem; font-weight: 800;
        line-height: 1.15; margin: 0; }
    .dashboard-subtitle { color: #c7c7c7; margin: .45rem 0 0; font-size: .92rem; }
    [data-testid="stMetric"] { background: #fff; padding: .85rem 1rem;
        border-bottom: 2px solid #E50914; }
    [data-testid="stMetricLabel"] { color: #737373; }
    [data-testid="stMetricValue"] { color: #141414; }
    h2, h3 { color: #141414; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    data_path = Path(__file__).resolve().parent / "netflix.csv"
    data = pd.read_csv(data_path, parse_dates=["Watch_Date"])
    required_columns = {
        "Watch_Date", "Region", "Subscription_Plan", "Rating",
        "Monthly_Revenue", "Category",
    }
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")
    return data


try:
    netflix = load_data()
except (FileNotFoundError, ValueError, KeyError) as error:
    st.error(f"Unable to load netflix.csv: {error}")
    st.stop()

st.sidebar.markdown("## NETFLIX")
st.sidebar.caption("VIEWING INSIGHTS")
minimum_date = netflix["Watch_Date"].min().date()
maximum_date = netflix["Watch_Date"].max().date()
selected_dates = st.sidebar.date_input(
    "Watch date range",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date,
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates

filtered = netflix[
    netflix["Watch_Date"].dt.date.between(start_date, end_date)
].copy()

st.markdown(
    """
    <div class="dashboard-head">
      <div class="dashboard-kicker">Netflix data analysis</div>
      <h1 class="dashboard-title">Viewing insights</h1>
      <p class="dashboard-subtitle">Engagement, ratings and revenue across your audience.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if filtered.empty:
    st.warning("No viewing records fall within this date range.")
    st.stop()

total_revenue = filtered["Monthly_Revenue"].sum()
average_rating = filtered["Rating"].mean()
watch_minutes = filtered["Watch_Time_Minutes"].sum() if "Watch_Time_Minutes" in filtered else None

metric_columns = st.columns(4)
metric_columns[0].metric("Viewing records", f"{len(filtered):,}")
metric_columns[1].metric("Total monthly revenue", f"{total_revenue:,.0f}")
metric_columns[2].metric("Average rating", f"{average_rating:.2f} / 5")
metric_columns[3].metric("Watch time", f"{watch_minutes:,.0f} min" if watch_minutes is not None else "N/A")

st.markdown("## Audience and revenue")
left_column, right_column = st.columns(2, gap="large")


def finish_figure(figure):
    figure.patch.set_facecolor("white")
    figure.tight_layout()
    st.pyplot(figure, width="stretch")
    plt.close(figure)


with left_column:
    st.markdown("### Revenue by region")
    region_revenue = filtered.groupby("Region")["Monthly_Revenue"].sum().sort_values(ascending=False)
    figure, axis = plt.subplots(figsize=(6, 3.8))
    bars = axis.bar(region_revenue.index, region_revenue.values, color=RED, width=0.62)
    axis.set_ylabel("Monthly revenue", color=MUTED)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color("#dedede")
    axis.tick_params(axis="y", left=False, labelcolor=MUTED)
    axis.tick_params(axis="x", bottom=False, labelcolor=INK)
    axis.grid(axis="y", color="#eeeeee", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.bar_label(bars, fmt="%.0f", padding=4, color=INK, fontsize=9)
    finish_figure(figure)

with right_column:
    st.markdown("### Rating total by subscription plan")
    plan_ratings = filtered.groupby("Subscription_Plan")["Rating"].sum().sort_values(ascending=False)
    figure, axis = plt.subplots(figsize=(6, 3.8))
    axis.pie(
        plan_ratings.values,
        labels=plan_ratings.index,
        colors=PALETTE[:len(plan_ratings)],
        startangle=90,
        counterclock=False,
        autopct="%1.0f%%",
        pctdistance=0.72,
        wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 2},
        textprops={"color": INK, "fontsize": 9},
    )
    axis.set_aspect("equal")
    finish_figure(figure)

left_column, right_column = st.columns(2, gap="large")

with left_column:
    st.markdown("### Rating distribution")
    rating_counts = filtered["Rating"].value_counts().sort_index()
    figure, axis = plt.subplots(figsize=(6, 3.8))
    bars = axis.bar(rating_counts.index.astype(str), rating_counts.values, color=INK, width=0.62)
    axis.set_xlabel("Rating", color=MUTED)
    axis.set_ylabel("Number of ratings", color=MUTED)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color("#dedede")
    axis.tick_params(axis="y", left=False, labelcolor=MUTED)
    axis.tick_params(axis="x", bottom=False, labelcolor=INK)
    axis.grid(axis="y", color="#eeeeee", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.bar_label(bars, padding=3, color=INK, fontsize=9)
    finish_figure(figure)

with right_column:
    st.markdown("### Revenue by category")
    category_revenue = filtered.groupby("Category")["Monthly_Revenue"].sum().sort_values(ascending=False)
    figure, axis = plt.subplots(figsize=(6, 3.8))
    wedges, _ = axis.pie(
        category_revenue.values,
        colors=[PALETTE[index % len(PALETTE)] for index in range(len(category_revenue))],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.4, "edgecolor": "white", "linewidth": 1.5},
    )
    legend_labels = [f"{name}  |  {value:,.0f}" for name, value in category_revenue.items()]
    axis.legend(
        wedges, legend_labels, title="Category  |  Revenue", loc="center left",
        bbox_to_anchor=(0.92, 0.5), frameon=False, fontsize=8,
        title_fontsize=8, labelcolor=INK,
    )
    axis.set_aspect("equal")
    finish_figure(figure)