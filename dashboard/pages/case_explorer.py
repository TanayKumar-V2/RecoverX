from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data import (
    get_batch_runs,
    get_case_details,
    get_cases,
)
from dashboard.ui import (
    display_label,
    format_inr,
    render_run_selector,
)

st.markdown(
    '<div class="revloop-eyebrow">Decision Trace</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="revloop-title">Case Explorer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="revloop-subtitle">'
    "Trace an individual payment from failure to financial outcome."
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
    key="case_explorer_run",
)

st.caption(
    f"Run ID: `{run_id}`"
)


# ---------------------------------------------------------------------------
# Load cases
# ---------------------------------------------------------------------------

cases = get_cases(run_id)

if not cases:
    st.warning(
        "No cases found for this run."
    )
    st.stop()

frame = pd.DataFrame(cases)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

filter_col1, filter_col2 = st.columns(
    [2, 1]
)

with filter_col1:
    search = st.text_input(
        "Search payment or customer",
        placeholder=(
            "Paste a payment UUID or customer ID..."
        ),
    )

with filter_col2:
    root_causes = sorted(
        {
            str(value)
            for value in frame[
                "root_cause"
            ].dropna()
        }
    )

    selected_root_cause = st.selectbox(
        "Root cause",
        options=["all"] + root_causes,
        format_func=lambda value: (
            "All root causes"
            if value == "all"
            else display_label(value)
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
    f"{len(filtered):,} matching payments"
)


if filtered.empty:
    st.info(
        "No payments match the selected filters."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Payment selection
# ---------------------------------------------------------------------------

case_options = filtered[
    "payment_id"
].tolist()


def format_case_option(
    payment_id: str,
) -> str:
    row = filtered[
        filtered["payment_id"]
        == payment_id
    ].iloc[0]

    root_cause = row["root_cause"]

    return (
        f"{payment_id[:8]}…  •  "
        f"₹{float(row['amount']):,.2f}  •  "
        f"{display_label(str(root_cause))}"
    )


selected_payment_id = st.selectbox(
    "Select payment",
    options=case_options,
    format_func=format_case_option,
)


details = get_case_details(
    run_id,
    str(selected_payment_id),
)

if details is None:
    st.error(
        "Unable to load the selected payment."
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


# ---------------------------------------------------------------------------
# Payment header
# ---------------------------------------------------------------------------

st.divider()

st.subheader("Payment overview")

payment_col1, payment_col2, payment_col3, payment_col4 = (
    st.columns(4)
)

with payment_col1:
    st.metric(
        "Payment amount",
        format_inr(
            float(payment["amount"])
        ),
    )

with payment_col2:
    st.metric(
        "Recovered",
        format_inr(
            sum(
                float(
                    attempt[
                        "amount_recovered"
                    ]
                )
                for attempt in recovery_attempts
            )
        ),
    )

with payment_col3:
    st.metric(
        "Decline code",
        str(
            payment["decline_code"]
        ),
    )

with payment_col4:
    outcome = (
        recovery_attempts[-1]["outcome"]
        if recovery_attempts
        else None
    )

    st.metric(
        "Outcome",
        display_label(
            str(outcome)
            if outcome is not None
            else None
        ),
    )

st.caption(
    f"Payment ID: `{payment['payment_id']}`"
)

st.caption(
    f"Customer ID: `{payment['customer_id']}`"
)


# ---------------------------------------------------------------------------
# Decision journey
# ---------------------------------------------------------------------------

st.divider()

st.subheader("Decision journey")

journey_1, journey_2, journey_3 = (
    st.columns(3)
)


with journey_1:
    st.markdown("### 01 · Diagnosis")

    if diagnosis is None:
        st.warning(
            "No diagnosis recorded."
        )
    else:
        st.write(
            "**Root cause**"
        )

        st.info(
            display_label(
                str(
                    diagnosis[
                        "root_cause"
                    ]
                )
            )
        )

        st.write(
            "**Source**"
        )

        st.write(
            display_label(
                str(
                    diagnosis[
                        "source"
                    ]
                )
            )
        )

        confidence = float(
            diagnosis[
                "confidence"
            ]
        )

        st.write(
            "**Confidence**"
        )

        st.progress(
            confidence,
            text=(
                f"{confidence:.0%}"
            ),
        )


with journey_2:
    st.markdown("### 02 · Policy")

    if audit_events:
        policy_events = [
            event
            for event in audit_events
            if event["event_type"]
            == "policy_decision"
        ]
    else:
        policy_events = []

    if not policy_events:
        st.warning(
            "No policy decision recorded."
        )
    else:
        policy = policy_events[-1]

        st.write(
            "**Decision**"
        )

        st.info(
            display_label(
                str(
                    policy["decision"]
                )
            )
        )

        st.write(
            "**Reason**"
        )

        st.write(
            policy["policy_reason"]
            or "No reason recorded."
        )

        allowed = (
            policy["metadata"]
            .get("allowed")
        )

        if allowed:
            st.success(
                "Action allowed"
            )
        else:
            st.error(
                "Action blocked"
            )


with journey_3:
    st.markdown("### 03 · Recovery")

    if not recovery_attempts:
        st.warning(
            "No recovery attempt recorded."
        )
    else:
        latest = recovery_attempts[-1]

        st.write(
            "**Action**"
        )

        st.info(
            display_label(
                str(
                    latest[
                        "action_type"
                    ]
                )
            )
        )

        st.write(
            "**Outcome**"
        )

        st.write(
            display_label(
                str(
                    latest[
                        "outcome"
                    ]
                )
            )
        )

        st.write(
            "**Amount recovered**"
        )

        st.metric(
            label="",
            value=format_inr(
                float(
                    latest[
                        "amount_recovered"
                    ]
                )
            ),
        )


# ---------------------------------------------------------------------------
# AI reasoning
# ---------------------------------------------------------------------------

if diagnosis is not None:
    st.divider()

    st.subheader(
        "Diagnosis reasoning"
    )

    source = str(
        diagnosis["source"]
    )

    if source == "llm":
        st.caption(
            "Generated by Cohere"
        )
    else:
        st.caption(
            "Generated by deterministic rule engine"
        )

    st.info(
        str(
            diagnosis["reasoning"]
        )
    )

    metadata_col1, metadata_col2, metadata_col3 = (
        st.columns(3)
    )

    with metadata_col1:
        model_name = diagnosis.get(
            "model_name"
        )

        st.write(
            f"**Model:** "
            f"{model_name or '—'}"
        )

    with metadata_col2:
        prompt_version = diagnosis.get(
            "prompt_version"
        )

        st.write(
            f"**Prompt:** "
            f"{prompt_version or '—'}"
        )

    with metadata_col3:
        latency = diagnosis.get(
            "latency_ms"
        )

        st.write(
            f"**Latency:** "
            f"{float(latency):.1f} ms"
            if latency is not None
            else "**Latency:** —"
        )


# ---------------------------------------------------------------------------
# Recovery history
# ---------------------------------------------------------------------------

st.divider()

st.subheader(
    "Recovery history"
)

if not recovery_attempts:
    st.info(
        "No recovery attempts were recorded."
    )
else:
    recovery_frame = pd.DataFrame(
        recovery_attempts
    )

    recovery_frame["Action"] = (
        recovery_frame[
            "action_type"
        ].map(
            lambda value:
            display_label(
                str(value)
            )
        )
    )

    recovery_frame["Outcome"] = (
        recovery_frame[
            "outcome"
        ].map(
            lambda value:
            display_label(
                str(value)
            )
        )
    )

    recovery_frame["Recovered"] = (
        recovery_frame[
            "amount_recovered"
        ].map(
            lambda value:
            format_inr(
                float(value)
            )
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
    ].rename(
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

st.subheader(
    "Audit trail"
)

if not audit_events:
    st.info(
        "No audit events recorded."
    )
else:
    for index, event in enumerate(
        audit_events
    ):
        event_name = display_label(
            str(
                event["event_type"]
            )
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
                    f"{display_label(str(event['decision']))}"
                )

            if event["policy_reason"]:
                st.write(
                    f"**Policy reason:** "
                    f"{event['policy_reason']}"
                )

            metadata = event[
                "metadata"
            ]

            if metadata:
                st.json(metadata)