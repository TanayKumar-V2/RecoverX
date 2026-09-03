from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from dashboard.data import (
    get_actions,
    get_batch_runs,
    get_outcomes,
    get_root_causes,
    get_run_summary,
)


st.title("RevLoop")
st.caption(
    "AI-assisted subscription payment recovery intelligence"
)


runs = get_batch_runs()

if not runs:
    st.warning(
        "No batch runs found. Run the RevLoop pipeline first."
    )
    st.stop()


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
        f"{run['started_at']} — "
        f"{run['run_id'][:8]}"
    )
    for run in completed_runs
]

selected_index = st.sidebar.selectbox(
    "Batch run",
    options=range(len(completed_runs)),
    format_func=lambda index: run_labels[index],
)

selected_run = completed_runs[selected_index]

run_id = str(selected_run["run_id"])

summary = get_run_summary(run_id)


st.caption(
    f"Run ID: `{run_id}`"
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Payments processed",
        f"{summary['total_payments']:,}",
    )

with col2:
    st.metric(
        "Revenue at risk",
        f"₹{summary['total_at_risk']:,.2f}",
    )

with col3:
    st.metric(
        "Revenue recovered",
        f"₹{summary['total_recovered']:,.2f}",
    )

with col4:
    st.metric(
        "Recovery rate",
        f"{summary['recovery_rate']:.2%}",
    )


st.divider()


st.subheader("Recovery performance")


left, right = st.columns(2)


with left:
    outcomes = get_outcomes(run_id)

    outcome_frame = pd.DataFrame(
        {
            "Outcome": list(outcomes.keys()),
            "Payments": list(outcomes.values()),
        }
    )

    st.bar_chart(
        outcome_frame,
        x="Outcome",
        y="Payments",
    )


with right:
    root_causes = get_root_causes(run_id)

    root_cause_frame = pd.DataFrame(
        {
            "Root cause": list(root_causes.keys()),
            "Payments": list(root_causes.values()),
        }
    )

    st.bar_chart(
        root_cause_frame,
        x="Root cause",
        y="Payments",
    )


st.divider()


st.subheader("Policy actions")

actions = get_actions(run_id)

action_frame = pd.DataFrame(
    {
        "Action": list(actions.keys()),
        "Payments": list(actions.values()),
    }
)

st.bar_chart(
    action_frame,
    x="Action",
    y="Payments",
)


st.divider()


st.subheader("Run details")

detail_col1, detail_col2, detail_col3 = st.columns(3)

with detail_col1:
    st.metric(
        "Successful recoveries",
        f"{summary['successful_recoveries']:,}",
    )

with detail_col2:
    st.metric(
        "Failed recoveries",
        f"{summary['failed_recoveries']:,}",
    )

with detail_col3:
    st.metric(
        "Pending / review",
        f"{summary['pending_recoveries']:,}",
    )


st.caption(
    "Metrics are calculated from the selected batch run."
)