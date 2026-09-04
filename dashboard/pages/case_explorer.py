from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data import (
    get_batch_runs,
    get_cases,
)

LABELS: dict[str, str] = {
    "insufficient_funds": "Insufficient funds",
    "expired_card": "Expired card",
    "hard_decline": "Hard decline",
    "soft_decline": "Soft decline",
    "fraud_flag": "Fraud flag",
    "transient_glitch": "Transient glitch",
    "rule": "Rule engine",
    "llm": "Cohere",
    "smart_retry": "Smart retry",
    "send_update_link": "Update payment method",
    "immediate_retry": "Immediate retry",
    "escalate_manual_review": "Manual review",
    "stop_no_action": "No action",
    "recovered": "Recovered",
    "failed": "Failed",
    "pending": "Pending",
}


def label(value: str | None) -> str:
    if value is None:
        return "—"

    return LABELS.get(
        value,
        value.replace("_", " ").title(),
    )


st.title("Case Explorer")

st.caption(
    "Inspect individual payment decisions from diagnosis "
    "through recovery."
)


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

selected_run_index = st.sidebar.selectbox(
    "Batch run",
    options=range(len(completed_runs)),
    format_func=lambda index: run_labels[index],
    key="case_explorer_run",
)

selected_run = completed_runs[
    selected_run_index
]

run_id = str(selected_run["run_id"])

cases = get_cases(run_id)

if not cases:
    st.warning(
        "No cases found for this batch run."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Case search/filter
# ---------------------------------------------------------------------------

frame = pd.DataFrame(cases)

search = st.text_input(
    "Search customer or payment ID",
    placeholder="CUST-1234 or UUID...",
)

root_causes = sorted(
    {
        str(value)
        for value in frame["root_cause"].dropna()
    }
)

selected_root_cause = st.selectbox(
    "Root cause",
    options=["all"] + root_causes,
    format_func=lambda value: (
        "All root causes"
        if value == "all"
        else label(value)
    ),
)


filtered = frame.copy()

if search:
    search_lower = search.lower()

    filtered = filtered[
        filtered["payment_id"]
        .str.lower()
        .str.contains(
            search_lower,
            regex=False,
        )
        |
        filtered["customer_id"]
        .str.lower()
        .str.contains(
            search_lower,
            regex=False,
        )
    ]

if selected_root_cause != "all":
    filtered = filtered[
        filtered["root_cause"]
        == selected_root_cause
    ]


st.caption(
    f"{len(filtered):,} cases"
)


if filtered.empty:
    st.info(
        "No cases match the current filters."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Case selector
# ---------------------------------------------------------------------------

case_options = filtered[
    "payment_id"
].tolist()

selected_payment_id = st.selectbox(
    "Select payment",
    options=case_options,
    format_func=lambda payment_id: (
        f"{str(payment_id)[:8]}…  •  "
        f"₹{filtered.loc[filtered['payment_id'] == payment_id, 'amount'].iloc[0]:,.2f}"
    ),
)


case = next(
    item
    for item in cases
    if item["payment_id"]
    == selected_payment_id
)


st.divider()


# ---------------------------------------------------------------------------
# Payment header
# ---------------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Payment amount",
        f"₹{float(case['amount']):,.2f}",
    )

with col2:
    st.metric(
        "Recovered",
        f"₹{float(case['amount_recovered']):,.2f}",
    )

with col3:
    outcome = case["outcome"]

    st.metric(
        "Outcome",
        label(
            str(outcome)
            if outcome is not None
            else None
        ),
    )


st.caption(
    f"Payment ID: `{case['payment_id']}`"
)

st.caption(
    f"Customer: `{case['customer_id']}`"
)


# ---------------------------------------------------------------------------
# Decision journey
# ---------------------------------------------------------------------------

st.subheader("Decision journey")

step1, step2, step3 = st.columns(3)

with step1:
    st.markdown("### 1 · Diagnosis")

    st.write(
        f"**Root cause:** "
        f"{label(case['root_cause'])}"
    )

    st.write(
        f"**Source:** "
        f"{label(case['diagnosis_source'])}"
    )

    confidence = case["confidence"]

    if confidence is not None:
        st.write(
            f"**Confidence:** "
            f"{float(confidence):.0%}"
        )

with step2:
    st.markdown("### 2 · Policy")

    st.write(
        f"**Action:** "
        f"{label(case['action'])}"
    )

with step3:
    st.markdown("### 3 · Recovery")

    st.write(
        f"**Outcome:** "
        f"{label(case['outcome'])}"
    )

    st.write(
        f"**Recovered:** "
        f"₹{float(case['amount_recovered']):,.2f}"
    )


st.divider()


st.info(
    "Detailed Cohere reasoning and the complete audit timeline "
    "will be shown here as the run-scoped case view is expanded."
)
