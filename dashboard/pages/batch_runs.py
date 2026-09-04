from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data import get_run_metrics

st.title("Batch Runs")

st.caption(
    "History and performance of RevLoop executions."
)


runs = get_run_metrics()

if not runs:
    st.info(
        "No batch runs are available yet."
    )
    st.stop()


frame = pd.DataFrame(runs)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

completed = frame[
    frame["status"] == "completed"
]

total_runs = len(frame)

successful_runs = len(completed)

average_recovery_rate = (
    completed["recovery_rate"].mean()
    if not completed.empty
    else 0.0
)

total_recovered = (
    completed["total_recovered"].sum()
    if not completed.empty
    else 0.0
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total runs",
        f"{total_runs:,}",
    )

with col2:
    st.metric(
        "Completed",
        f"{successful_runs:,}",
    )

with col3:
    st.metric(
        "Avg. recovery rate",
        f"{average_recovery_rate:.2%}",
    )

with col4:
    st.metric(
        "Revenue recovered",
        f"₹{total_recovered:,.2f}",
    )


st.divider()


# ---------------------------------------------------------------------------
# Run history
# ---------------------------------------------------------------------------

st.subheader("Run history")

display_frame = frame.copy()

display_frame["Run ID"] = display_frame[
    "run_id"
].str.slice(0, 8) + "…"

display_frame["Started"] = (
    pd.to_datetime(
        display_frame["started_at"]
    )
    .dt.strftime(
        "%d %b %Y, %H:%M"
    )
)

display_frame["Status"] = (
    display_frame["status"]
    .str.title()
)

display_frame["Payments"] = (
    display_frame["total_payments"]
)

display_frame["At risk"] = (
    display_frame["total_at_risk"]
    .map(
        lambda value:
        f"₹{float(value):,.2f}"
    )
)

display_frame["Recovered"] = (
    display_frame["total_recovered"]
    .map(
        lambda value:
        f"₹{float(value):,.2f}"
    )
)

display_frame["Recovery rate"] = (
    display_frame["recovery_rate"]
    .map(
        lambda value:
        f"{float(value):.2%}"
    )
)

display_frame = display_frame[
    [
        "Run ID",
        "Started",
        "Status",
        "Payments",
        "At risk",
        "Recovered",
        "Recovery rate",
    ]
]

st.dataframe(
    display_frame,
    width="stretch",
    hide_index=True,
)


st.divider()


# ---------------------------------------------------------------------------
# Recovery rate across runs
# ---------------------------------------------------------------------------

st.subheader("Recovery rate across runs")

chart_frame = frame[
    [
        "started_at",
        "recovery_rate",
    ]
].copy()

chart_frame["Run"] = (
    pd.to_datetime(
        chart_frame["started_at"]
    )
    .dt.strftime(
        "%d %b %H:%M"
    )
)

chart_frame = chart_frame[
    [
        "Run",
        "recovery_rate",
    ]
]

chart_frame["recovery_rate"] *= 100

chart_frame = chart_frame.sort_values(
    "Run"
)

chart_frame = chart_frame.rename(
    columns={
        "recovery_rate": "Recovery rate (%)"
    }
)

st.bar_chart(
    chart_frame,
    x="Run",
    y="Recovery rate (%)",
    height=320,
)


st.divider()


# ---------------------------------------------------------------------------
# Revenue recovered across runs
# ---------------------------------------------------------------------------

st.subheader("Revenue recovered across runs")

revenue_frame = frame[
    [
        "started_at",
        "total_recovered",
    ]
].copy()

revenue_frame["Run"] = (
    pd.to_datetime(
        revenue_frame["started_at"]
    )
    .dt.strftime(
        "%d %b %H:%M"
    )
)

revenue_frame = revenue_frame[
    [
        "Run",
        "total_recovered",
    ]
].rename(
    columns={
        "total_recovered": "Recovered revenue"
    }
)

st.bar_chart(
    revenue_frame,
    x="Run",
    y="Recovered revenue",
    height=320,
)