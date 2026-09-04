from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data import (
    get_actions,
    get_batch_runs,
    get_outcomes,
    get_root_causes,
    get_run_summary,
)

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

LABELS: dict[str, str] = {
    # Root causes
    "insufficient_funds": "Insufficient funds",
    "expired_card": "Expired card",
    "hard_decline": "Hard decline",
    "soft_decline": "Soft decline",
    "fraud_flag": "Fraud flag",
    "transient_glitch": "Transient glitch",
    # Actions
    "smart_retry": "Smart retry",
    "send_update_link": "Update payment method",
    "immediate_retry": "Immediate retry",
    "escalate_manual_review": "Manual review",
    "stop_no_action": "No action",
    # Outcomes
    "recovered": "Recovered",
    "failed": "Failed",
    "pending": "Pending",
}


def display_label(value: str) -> str:
    """Convert internal enum-style values into user-friendly labels."""
    return LABELS.get(
        value,
        value.replace("_", " ").title(),
    )


def compact_currency(value: float) -> str:
    """Format INR using lakh/crore-friendly notation."""
    if value >= 10_000_000:
        return f"₹{value / 10_000_000:.2f}Cr"

    if value >= 100_000:
        return f"₹{value / 100_000:.2f}L"

    if value >= 1_000:
        return f"₹{value / 1_000:.1f}K"

    return f"₹{value:,.0f}"


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.title("RevLoop")
st.caption(
    "AI-assisted subscription payment recovery intelligence"
)


# ---------------------------------------------------------------------------
# Batch selector
# ---------------------------------------------------------------------------

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
        f"{run['started_at']}  •  "
        f"{str(run['run_id'])[:8]}"
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


# ---------------------------------------------------------------------------
# Run metadata
# ---------------------------------------------------------------------------

header_left, header_right = st.columns(
    [4, 1],
    vertical_alignment="center",
)

with header_left:
    st.caption(
        f"Run ID: `{run_id}`"
    )

with header_right:
    st.success(
        "COMPLETED",
        icon=":material/check_circle:",
    )


# ---------------------------------------------------------------------------
# Executive KPIs
# ---------------------------------------------------------------------------

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)

with kpi_1:
    st.metric(
        "Payments processed",
        f"{summary['total_payments']:,}",
    )

with kpi_2:
    st.metric(
        "Revenue at risk",
        f"₹{summary['total_at_risk']:,.2f}",
    )

with kpi_3:
    st.metric(
        "Revenue recovered",
        f"₹{summary['total_recovered']:,.2f}",
    )

with kpi_4:
    st.metric(
        "Recovery rate",
        f"{summary['recovery_rate']:.2%}",
    )


# ---------------------------------------------------------------------------
# Executive insight
# ---------------------------------------------------------------------------

recovery_rate = float(
    summary["recovery_rate"]
)

recovered = float(
    summary["total_recovered"]
)

at_risk = float(
    summary["total_at_risk"]
)

st.info(
    f"**Recovery insight:** "
    f"{compact_currency(recovered)} recovered from "
    f"{compact_currency(at_risk)} at risk "
    f"({recovery_rate:.2%} recovery rate)."
)


st.divider()


# ---------------------------------------------------------------------------
# Recovery performance
# ---------------------------------------------------------------------------

st.subheader("Recovery performance")

outcomes = get_outcomes(run_id)
root_causes = get_root_causes(run_id)

left, right = st.columns(2)

with left:
    st.markdown("#### Recovery outcomes")

    outcome_frame = pd.DataFrame(
        {
            "Outcome": [
                display_label(value)
                for value in outcomes
            ],
            "Payments": list(
                outcomes.values()
            ),
        }
    )

    outcome_frame = outcome_frame.sort_values(
        "Payments",
        ascending=True,
    )

    st.bar_chart(
        outcome_frame,
        x="Outcome",
        y="Payments",
        horizontal=True,
        height=280,
    )


with right:
    st.markdown("#### Root causes")

    root_cause_frame = pd.DataFrame(
        {
            "Root cause": [
                display_label(value)
                for value in root_causes
            ],
            "Payments": list(
                root_causes.values()
            ),
        }
    )

    root_cause_frame = root_cause_frame.sort_values(
        "Payments",
        ascending=True,
    )

    st.bar_chart(
        root_cause_frame,
        x="Root cause",
        y="Payments",
        horizontal=True,
        height=280,
    )


st.divider()


# ---------------------------------------------------------------------------
# Policy actions
# ---------------------------------------------------------------------------

st.subheader("Policy actions")

actions = get_actions(run_id)

action_frame = pd.DataFrame(
    {
        "Action": [
            display_label(value)
            for value in actions
        ],
        "Payments": list(
            actions.values()
        ),
    }
)

action_frame = action_frame.sort_values(
    "Payments",
    ascending=True,
)

st.bar_chart(
    action_frame,
    x="Action",
    y="Payments",
    horizontal=True,
    height=300,
)


st.divider()


# ---------------------------------------------------------------------------
# Recovery summary cards
# ---------------------------------------------------------------------------

st.subheader("Run details")

detail_1, detail_2, detail_3 = st.columns(3)

with detail_1:
    st.metric(
        "Successful recoveries",
        f"{summary['successful_recoveries']:,}",
    )

with detail_2:
    st.metric(
        "Failed recoveries",
        f"{summary['failed_recoveries']:,}",
    )

with detail_3:
    st.metric(
        "Pending recovery",
        f"{summary['pending_recoveries']:,}",
    )


# ---------------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------------

with st.expander("How these metrics are calculated"):
    st.markdown(
        """
        **Revenue at risk** is the total payment value included in
        the selected batch run.

        **Revenue recovered** is the sum of simulated recovery amounts
        produced by successful recovery attempts.

        **Recovery rate** is:

        `revenue recovered / revenue at risk`

        All metrics above are filtered to the selected batch run using
        its unique `run_id`.
        """
    )