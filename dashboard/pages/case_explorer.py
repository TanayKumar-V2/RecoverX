from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data import (
    get_batch_runs,
    get_case_details,
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
    "Trace an individual payment through diagnosis, policy, "
    "recovery, and audit history."
)


# ---------------------------------------------------------------------------
# Run selection
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

st.caption(
    f"Run ID: `{run_id}`"
)


# ---------------------------------------------------------------------------
# Load cases
# ---------------------------------------------------------------------------

cases = get_cases(run_id)

if not cases:
    st.warning(
        "No cases found for this batch run."
    )
    st.stop()


frame = pd.DataFrame(cases)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

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
    f"{len(filtered):,} matching cases"
)


if filtered.empty:
    st.info(
        "No cases match the current filters."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Payment selection
# ---------------------------------------------------------------------------

case_options = filtered[
    "payment_id"
].tolist()


def case_label(payment_id: str) -> str:
    row = filtered[
        filtered["payment_id"]
        == payment_id
    ].iloc[0]

    return (
        f"{str(payment_id)[:8]}…  •  "
        f"₹{float(row['amount']):,.2f}  •  "
        f"{label(str(row['root_cause']))}"
    )


selected_payment_id = st.selectbox(
    "Select payment",
    options=case_options,
    format_func=case_label,
)


details = get_case_details(
    run_id,
    str(selected_payment_id),
)

if details is None:
    st.error(
        "Unable to load the selected case."
    )
    st.stop()


payment = details["payment"]
diagnosis = details["diagnosis"]
recovery_attempts = details[
    "recovery_attempts"
]
audit_events = details[
    "audit_events"
]


st.divider()


# ---------------------------------------------------------------------------
# Payment summary
# ---------------------------------------------------------------------------

st.subheader("Payment")

payment_col1, payment_col2, payment_col3, payment_col4 = (
    st.columns(4)
)

with payment_col1:
    st.metric(
        "Amount",
        f"₹{float(payment['amount']):,.2f}",
    )

with payment_col2:
    st.metric(
        "Customer",
        str(payment["customer_id"]),
    )

with payment_col3:
    st.metric(
        "Decline code",
        str(payment["decline_code"]),
    )

with payment_col4:
    total_recovered = sum(
        float(
            attempt["amount_recovered"]
        )
        for attempt in recovery_attempts
    )

    st.metric(
        "Recovered",
        f"₹{total_recovered:,.2f}",
    )


st.caption(
    f"Payment ID: `{payment['payment_id']}`"
)


# ---------------------------------------------------------------------------
# Diagnosis
# ---------------------------------------------------------------------------

st.divider()

st.subheader("Diagnosis")

if diagnosis is None:
    st.warning(
        "No diagnosis record exists for this payment in this run."
    )
else:
    diagnosis_col1, diagnosis_col2, diagnosis_col3 = (
        st.columns(3)
    )

    with diagnosis_col1:
        st.write(
            f"**Root cause:** "
            f"{label(str(diagnosis['root_cause']))}"
        )

    with diagnosis_col2:
        st.write(
            f"**Source:** "
            f"{label(str(diagnosis['source']))}"
        )

    with diagnosis_col3:
        confidence = diagnosis["confidence"]

        st.write(
            f"**Confidence:** "
            f"{float(confidence):.0%}"
        )

    st.markdown("#### Reasoning")

    st.info(
        str(
            diagnosis["reasoning"]
        )
    )

    if diagnosis.get("model_name"):
        st.caption(
            f"Model: `{diagnosis['model_name']}`"
        )

    if diagnosis.get("prompt_version"):
        st.caption(
            f"Prompt version: `{diagnosis['prompt_version']}`"
        )

    if diagnosis.get("latency_ms") is not None:
        st.caption(
            f"Latency: "
            f"{float(diagnosis['latency_ms']):.1f} ms"
        )


# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------

st.divider()

st.subheader("Recovery")

if not recovery_attempts:
    st.info(
        "No recovery attempt was recorded."
    )
else:
    recovery_frame = pd.DataFrame(
        recovery_attempts
    )

    recovery_frame["Outcome"] = (
        recovery_frame["outcome"]
        .map(
            lambda value: label(
                str(value)
            )
        )
    )

    recovery_frame["Action"] = (
        recovery_frame["action_type"]
        .map(
            lambda value: label(
                str(value)
            )
        )
    )

    recovery_frame["Recovered"] = (
        recovery_frame[
            "amount_recovered"
        ]
        .map(
            lambda value:
            f"₹{float(value):,.2f}"
        )
    )

    recovery_frame = recovery_frame[
        [
            "attempt_number",
            "Action",
            "Outcome",
            "Recovered",
            "timestamp",
            "policy_reason",
        ]
    ]

    recovery_frame = recovery_frame.rename(
        columns={
            "attempt_number": "Attempt",
            "timestamp": "Timestamp",
            "policy_reason": "Policy reason",
        }
    )

    st.dataframe(
        recovery_frame,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

st.divider()

st.subheader("Audit trail")

if not audit_events:
    st.info(
        "No audit events recorded."
    )
else:
    for index, event in enumerate(
        audit_events
    ):
        event_name = label(
            str(event["event_type"])
        )

        with st.expander(
            (
                f"{event['timestamp']}  •  "
                f"{event_name}"
            ),
            expanded=index == 0,
        ):
            st.write(
                f"**Actor:** "
                f"{event['actor']}"
            )

            if event["decision"]:
                st.write(
                    f"**Decision:** "
                    f"{label(str(event['decision']))}"
                )

            if event["policy_reason"]:
                st.write(
                    f"**Policy reason:** "
                    f"{event['policy_reason']}"
                )

            metadata = event["metadata"]

            if metadata:
                st.json(metadata)