from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data import (
    get_batch_runs,
    get_root_cause_financials,
    get_root_cause_insights,
)
from dashboard.ui import (
    display_label,
    format_inr,
    format_percent,
    render_run_selector,
)

st.markdown(
    '<div class="revloop-eyebrow">Financial Diagnostics</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="revloop-title">Root Cause Analysis</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="revloop-subtitle">'
    "Identify where revenue is being lost and where recovery works."
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Run selection
# ---------------------------------------------------------------------------

runs = get_batch_runs()

if not runs:
    st.warning(
        "No batch runs found."
    )
    st.stop()

run_id = render_run_selector(
    runs,
    key="root_cause_run",
)

st.caption(
    f"Run ID: `{run_id}`"
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

metrics = get_root_cause_financials(
    run_id
)

insights = get_root_cause_insights(
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
# Executive insights
# ---------------------------------------------------------------------------

st.subheader("Key insights")

insight_columns = st.columns(3)

for column, insight in zip(
    insight_columns,
    insights,
):
    root_cause = str(
        insight["root_cause"]
    )

    value = float(
        insight["value"]
    )

    with column:
        if insight["label"] == (
            "Best recovery rate"
        ):
            display_value = format_percent(
                value
            )
        else:
            display_value = format_inr(
                value
            )

        st.metric(
            insight["label"],
            display_value,
            help=(
                f"Root cause: "
                f"{display_label(root_cause)}"
            ),
        )

        st.caption(
            display_label(root_cause)
        )


st.divider()


# ---------------------------------------------------------------------------
# Financial exposure
# ---------------------------------------------------------------------------

st.subheader("Financial exposure by root cause")

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
    height=380,
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

effectiveness_frame = effectiveness_frame.rename(
    columns={
        "recovery_rate": "Recovery rate (%)"
    }
)

st.bar_chart(
    effectiveness_frame,
    x="Root cause",
    y="Recovery rate (%)",
    horizontal=True,
    height=330,
)


st.divider()


# ---------------------------------------------------------------------------
# Detailed table
# ---------------------------------------------------------------------------

st.subheader("Root cause performance")

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
    lambda value: format_inr(
        float(value)
    )
)

detail_frame["Recovered"] = detail_frame[
    "Recovered"
].map(
    lambda value: format_inr(
        float(value)
    )
)

detail_frame["Recovery rate"] = detail_frame[
    "Recovery rate"
].map(
    lambda value: format_percent(
        float(value)
    )
)

st.dataframe(
    detail_frame,
    width="stretch",
    hide_index=True,
)


with st.expander(
    "How to interpret this analysis"
):
    st.markdown(
        """
        **Largest revenue exposure** identifies the failure type
        associated with the greatest payment value.

        **Best recovery rate** identifies the failure type where
        RevLoop currently recovers the largest share of revenue at risk.

        **Largest unrecovered opportunity** identifies the failure type
        with the greatest remaining financial exposure after simulated
        recovery.

        These metrics are scoped to the selected batch run.
        """
    )