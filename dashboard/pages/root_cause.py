
from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data import (
    get_batch_runs,
    get_root_cause_financials,
)

LABELS: dict[str, str] = {
    "insufficient_funds": "Insufficient funds",
    "expired_card": "Expired card",
    "hard_decline": "Hard decline",
    "soft_decline": "Soft decline",
    "fraud_flag": "Fraud flag",
    "transient_glitch": "Transient glitch",
}


def display_label(value: str) -> str:
    return LABELS.get(
        value,
        value.replace("_", " ").title(),
    )


st.title("Root Cause Analysis")

st.caption(
    "Understand which payment failure types "
    "create the greatest recovery opportunity."
)


# ---------------------------------------------------------------------------
# Batch selection
# ---------------------------------------------------------------------------

runs = get_batch_runs()

completed_runs = [
    run
    for run in runs
    if run["status"] == "completed"
]

if not completed_runs:
    st.warning(
        "No completed batch runs are available."
    )
    st.stop()


run_labels = [
    (
        f"{run['started_at']}  •  "
        f"{str(run['run_id'])[:8]}"
    )
    for run in completed_runs
]

selected_index = st.sidebar.selectbox(
    "Batch run",
    options=range(len(completed_runs)),
    format_func=lambda index: run_labels[index],
    key="root_cause_run",
)

selected_run = completed_runs[selected_index]

run_id = str(selected_run["run_id"])

st.caption(
    f"Run ID: `{run_id}`"
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

metrics = get_root_cause_financials(
    run_id
)

if not metrics:
    st.warning(
        "No diagnosis data is available for this run."
    )
    st.stop()


frame = pd.DataFrame(metrics)

frame["Root cause"] = frame[
    "root_cause"
].map(display_label)


frame["Recovery rate"] = (
    frame["recovery_rate"] * 100
)


# ---------------------------------------------------------------------------
# Top opportunity
# ---------------------------------------------------------------------------

top_opportunity = frame.iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Largest revenue exposure",
        display_label(
            str(top_opportunity["root_cause"])
        ),
    )

with col2:
    st.metric(
        "Revenue at risk",
        f"₹{top_opportunity['at_risk']:,.2f}",
    )

with col3:
    st.metric(
        "Recovered from cause",
        f"₹{top_opportunity['recovered']:,.2f}",
    )


st.divider()


# ---------------------------------------------------------------------------
# Financial exposure
# ---------------------------------------------------------------------------

st.subheader("Revenue exposure by root cause")

exposure_frame = frame[
    [
        "Root cause",
        "at_risk",
        "recovered",
    ]
].copy()

exposure_frame = exposure_frame.sort_values(
    "at_risk",
    ascending=True,
)

exposure_frame = exposure_frame.rename(
    columns={
        "at_risk": "At risk",
        "recovered": "Recovered",
    }
)

st.bar_chart(
    exposure_frame,
    x="Root cause",
    y=[
        "At risk",
        "Recovered",
    ],
    horizontal=True,
    height=350,
)


st.divider()


# ---------------------------------------------------------------------------
# Recovery effectiveness
# ---------------------------------------------------------------------------

st.subheader("Recovery effectiveness")

effectiveness_frame = frame[
    [
        "Root cause",
        "recovery_rate",
    ]
].copy()

effectiveness_frame = effectiveness_frame.sort_values(
    "recovery_rate",
    ascending=True,
)

effectiveness_frame[
    "Recovery rate"
] = effectiveness_frame[
    "recovery_rate"
]

st.bar_chart(
    effectiveness_frame,
    x="Root cause",
    y="Recovery rate",
    horizontal=True,
    height=300,
)


st.divider()


# ---------------------------------------------------------------------------
# Detailed table
# ---------------------------------------------------------------------------

st.subheader("Root cause detail")

detail_frame = frame[
    [
        "Root cause",
        "payments",
        "at_risk",
        "recovered",
        "Recovery rate",
    ]
].copy()

detail_frame = detail_frame.rename(
    columns={
        "payments": "Payments",
        "at_risk": "At risk",
        "recovered": "Recovered",
    }
)

detail_frame["At risk"] = detail_frame[
    "At risk"
].map(
    lambda value: f"₹{value:,.2f}"
)

detail_frame["Recovered"] = detail_frame[
    "Recovered"
].map(
    lambda value: f"₹{value:,.2f}"
)

detail_frame["Recovery rate"] = detail_frame[
    "Recovery rate"
].map(
    lambda value: f"{value:.2f}%"
)

st.dataframe(
    detail_frame,
    use_container_width=True,
    hide_index=True,
)


with st.expander("How to interpret this page"):
    st.markdown(
        """
        **At risk** represents the total payment value associated with
        each diagnosed root cause in the selected batch.

        **Recovered** represents the simulated revenue recovered from
        those payments during the same batch run.

        **Recovery rate** is recovered revenue divided by revenue at risk.

        A root cause with high exposure but low recovery rate represents
        a potentially important area for improving recovery policy.
        """
    )