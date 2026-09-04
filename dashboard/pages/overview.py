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
from dashboard.ui import (
    display_label,
    format_inr,
    format_inr_compact,
    format_percent,
    render_run_selector,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="revloop-eyebrow">Payment Recovery Intelligence</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="revloop-title">RevLoop</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="revloop-subtitle">'
    "AI-assisted subscription payment recovery"
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Run selection
# ---------------------------------------------------------------------------

runs = get_batch_runs()

if not runs:
    st.warning(
        "No batch runs found. Run the RevLoop pipeline first."
    )
    st.stop()

run_id = render_run_selector(
    runs,
    key="overview_run",
)

summary = get_run_summary(run_id)


# ---------------------------------------------------------------------------
# Run status
# ---------------------------------------------------------------------------

meta_left, meta_right = st.columns(
    [5, 1],
    vertical_alignment="center",
)

with meta_left:
    st.caption(
        f"Run ID: `{run_id}`"
    )

with meta_right:
    st.success(
        "Completed",
        icon=":material/check_circle:",
    )


# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

payments = int(
    summary["total_payments"]
)

at_risk = float(
    summary["total_at_risk"]
)

recovered = float(
    summary["total_recovered"]
)

recovery_rate = float(
    summary["recovery_rate"]
)

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)

with kpi_1:
    st.metric(
        "Payments processed",
        f"{payments:,}",
    )

with kpi_2:
    st.metric(
        "Revenue at risk",
        format_inr(at_risk),
    )

with kpi_3:
    st.metric(
        "Revenue recovered",
        format_inr(recovered),
    )

with kpi_4:
    st.metric(
        "Recovery rate",
        format_percent(recovery_rate),
    )


# ---------------------------------------------------------------------------
# Executive insight
# ---------------------------------------------------------------------------

unrecovered = max(
    at_risk - recovered,
    0.0,
)

st.info(
    f"**Batch insight:** "
    f"{format_inr_compact(recovered)} recovered from "
    f"{format_inr_compact(at_risk)} at risk, leaving "
    f"{format_inr_compact(unrecovered)} unrecovered.",
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
    ).sort_values(
        "Payments",
        ascending=True,
    )

    st.bar_chart(
        outcome_frame,
        x="Outcome",
        y="Payments",
        horizontal=True,
        height=290,
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
    ).sort_values(
        "Payments",
        ascending=True,
    )

    st.bar_chart(
        root_cause_frame,
        x="Root cause",
        y="Payments",
        horizontal=True,
        height=290,
    )


st.divider()


# ---------------------------------------------------------------------------
# Policy actions
# ---------------------------------------------------------------------------

st.subheader("Policy decisions")

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
).sort_values(
    "Payments",
    ascending=True,
)

st.bar_chart(
    action_frame,
    x="Action",
    y="Payments",
    horizontal=True,
    height=320,
)


st.divider()


# ---------------------------------------------------------------------------
# Recovery statistics
# ---------------------------------------------------------------------------

st.subheader("Run statistics")

detail_1, detail_2, detail_3 = st.columns(3)

with detail_1:
    st.metric(
        "Successful recoveries",
        f"{int(summary['successful_recoveries']):,}",
    )

with detail_2:
    st.metric(
        "Failed recoveries",
        f"{int(summary['failed_recoveries']):,}",
    )

with detail_3:
    st.metric(
        "Pending recovery",
        f"{int(summary['pending_recoveries']):,}",
    )


# ---------------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------------

with st.expander("How RevLoop calculates these metrics"):
    st.markdown(
        """
        **Revenue at risk** is the total value of failed payments
        included in the selected batch.

        **Revenue recovered** is the total simulated payment value
        recovered by successful recovery attempts.

        **Recovery rate** is:

        `revenue recovered / revenue at risk`

        All metrics on this page are scoped to the selected `run_id`.
        """
    )