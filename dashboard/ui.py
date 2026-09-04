from __future__ import annotations

from collections.abc import Mapping

import streamlit as st

LABELS: dict[str, str] = {
    # Root causes
    "insufficient_funds": "Insufficient funds",
    "expired_card": "Expired card",
    "hard_decline": "Hard decline",
    "soft_decline": "Soft decline",
    "fraud_flag": "Fraud flag",
    "transient_glitch": "Transient glitch",
    # Sources
    "rule": "Rule engine",
    "llm": "Cohere",
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
    # Event types
    "diagnosis": "Diagnosis",
    "policy_decision": "Policy decision",
    "recovery_attempt": "Recovery attempt",
    "escalation": "Escalation",
    "stop": "Stop",
    "recovery": "Recovery",
}


def display_label(value: str | None) -> str:
    if value is None:
        return "—"

    return LABELS.get(
        value,
        value.replace("_", " ").title(),
    )


def format_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def format_inr_compact(value: float) -> str:
    if value >= 10_000_000:
        return f"₹{value / 10_000_000:.2f}Cr"

    if value >= 100_000:
        return f"₹{value / 100_000:.2f}L"

    if value >= 1_000:
        return f"₹{value / 1_000:.1f}K"

    return f"₹{value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value:.2%}"


def render_run_selector(
    runs: list[dict[str, object]],
    *,
    key: str,
) -> str:
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

    labels = [
        (
            f"{run['started_at']}  •  "
            f"{str(run['run_id'])[:8]}"
        )
        for run in completed_runs
    ]

    selected_index = st.sidebar.selectbox(
        "Batch run",
        options=range(len(completed_runs)),
        format_func=lambda index: labels[index],
        key=key,
    )

    selected_run = completed_runs[selected_index]

    return str(selected_run["run_id"])


def render_metric_card(
    label: str,
    value: str,
    help_text: str | None = None,
) -> None:
    st.metric(
        label=label,
        value=value,
        help=help_text,
    )


def humanize_dict(
    values: Mapping[str, int],
) -> dict[str, int]:
    return {
        display_label(key): value
        for key, value in values.items()
    }