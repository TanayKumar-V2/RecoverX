from __future__ import annotations

from uuid import UUID

import streamlit as st

from app.core.database import SessionLocal
from app.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.repositories.batch_run_repository import (
    BatchRunRepository,
)


@st.cache_data(ttl=10)
def get_batch_runs() -> list[dict[str, object]]:
    with SessionLocal() as session:
        repository = BatchRunRepository(session)

        runs = repository.list_all()

        return [
            {
                "run_id": str(run.run_id),
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "status": run.status,
            }
            for run in runs
        ]


@st.cache_data(ttl=10)
def get_run_summary(
    run_id: str,
) -> dict[str, object]:
    with SessionLocal() as session:
        repository = AnalyticsRepository(session)

        summary = repository.get_run_summary(
            UUID(run_id)
        )

        return {
            "run_id": str(summary.run_id),
            "total_payments": summary.total_payments,
            "total_at_risk": summary.total_at_risk,
            "total_recovered": summary.total_recovered,
            "recovery_rate": summary.recovery_rate,
            "successful_recoveries": (
                summary.successful_recoveries
            ),
            "failed_recoveries": (
                summary.failed_recoveries
            ),
            "pending_recoveries": (
                summary.pending_recoveries
            ),
        }


@st.cache_data(ttl=10)
def get_root_causes(
    run_id: str,
) -> dict[str, int]:
    with SessionLocal() as session:
        repository = AnalyticsRepository(session)

        return repository.get_root_cause_breakdown(
            UUID(run_id)
        )


@st.cache_data(ttl=10)
def get_actions(
    run_id: str,
) -> dict[str, int]:
    with SessionLocal() as session:
        repository = AnalyticsRepository(session)

        return repository.get_action_breakdown(
            UUID(run_id)
        )


@st.cache_data(ttl=10)
def get_outcomes(
    run_id: str,
) -> dict[str, int]:
    with SessionLocal() as session:
        repository = AnalyticsRepository(session)

        return repository.get_recovery_outcome_breakdown(
            UUID(run_id)
        )


@st.cache_data(ttl=10)
def get_root_cause_financials(
    run_id: str,
) -> list[dict[str, object]]:
    with SessionLocal() as session:
        repository = AnalyticsRepository(
            session
        )

        metrics = (
            repository.get_root_cause_financials(
                UUID(run_id)
            )
        )

        return [
            {
                "root_cause": metric.root_cause,
                "payments": metric.payments,
                "at_risk": metric.at_risk,
                "recovered": metric.recovered,
                "recovery_rate": metric.recovery_rate,
            }
            for metric in metrics
        ]


@st.cache_data(ttl=10)
def get_cases(
    run_id: str,
) -> list[dict[str, object]]:
    with SessionLocal() as session:
        repository = AnalyticsRepository(
            session
        )

        cases = repository.get_cases_for_run(
            UUID(run_id)
        )

        return [
            {
                "payment_id": str(case.payment_id),
                "customer_id": case.customer_id,
                "amount": case.amount,
                "decline_code": case.decline_code,
                "root_cause": case.root_cause,
                "diagnosis_source": case.diagnosis_source,
                "confidence": case.confidence,
                "action": case.action,
                "outcome": case.outcome,
                "amount_recovered": (
                    case.amount_recovered
                ),
            }
            for case in cases
        ]