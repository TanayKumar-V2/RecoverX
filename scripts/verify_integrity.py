from __future__ import annotations

import random
from uuid import UUID

from app.core.database import SessionLocal
from app.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.diagnosis_repository import (
    DiagnosisRepository,
)
from app.repositories.recovery_repository import (
    RecoveryRepository,
)
from dashboard.data import (
    get_actions,
    get_batch_runs,
    get_case_details,
    get_cases,
    get_outcomes,
    get_root_cause_financials,
    get_root_cause_insights,
    get_root_causes,
    get_run_metrics,
    get_run_summary,
)


def verify_overview() -> str:
    print("=== OVERVIEW: selected-run KPIs ===")

    runs = get_batch_runs()

    print(f"Total runs in DB: {len(runs)}")

    for run in runs[:3]:
        print(
            f"  {str(run['run_id'])[:8]} "
            f"{run['status']} "
            f"started {run['started_at']}"
        )

    metrics = get_run_metrics()

    latest = metrics[0] if metrics else None

    if latest is None:
        raise RuntimeError(
            "No batch-run metrics found."
        )

    run_id = str(latest["run_id"])

    print(f"\nLatest run_id: {run_id}")
    print(
        f"  total_payments: "
        f"{latest['total_payments']}"
    )
    print(
        f"  total_at_risk: "
        f"{float(latest['total_at_risk']):.2f}"
    )
    print(
        f"  total_recovered: "
        f"{float(latest['total_recovered']):.2f}"
    )
    print(
        f"  recovery_rate: "
        f"{float(latest['recovery_rate']):.2%}"
    )

    summary = get_run_summary(run_id)

    print("\nDirect summary for same run:")
    print(f"  {summary}")

    assert (
        summary["total_payments"]
        == latest["total_payments"]
    )

    assert (
        abs(
            float(summary["total_at_risk"])
            - float(latest["total_at_risk"])
        )
        < 0.01
    )

    assert (
        abs(
            float(summary["total_recovered"])
            - float(latest["total_recovered"])
        )
        < 0.01
    )

    print(
        "  -> KPIs MATCH between "
        "get_run_metrics and get_run_summary"
    )

    with SessionLocal() as session:
        repository = AnalyticsRepository(
            session
        )

        raw_summary = repository.get_run_summary(
            UUID(run_id)
        )

        print(
            "Raw DB summary: "
            f"payments={raw_summary.total_payments} "
            f"at_risk={raw_summary.total_at_risk:.2f} "
            f"recovered={raw_summary.total_recovered:.2f}"
        )

        assert (
            raw_summary.total_payments
            == summary["total_payments"]
        )

    print("OVERVIEW PASS")

    return run_id


def verify_root_cause(run_id: str) -> None:
    print()
    print("=== ROOT CAUSE ANALYSIS ===")

    root_causes = get_root_causes(run_id)
    actions = get_actions(run_id)
    outcomes = get_outcomes(run_id)
    financials = get_root_cause_financials(run_id)
    insights = get_root_cause_insights(run_id)

    print(f"Root causes: {root_causes}")
    print(f"Actions: {actions}")
    print(f"Outcomes: {outcomes}")
    print(
        f"Financials count: "
        f"{len(financials)}"
    )

    for financial in financials[:3]:
        print(f"  {financial}")

    print(f"Insights: {insights}")

    if financials:
        sum_at_risk = sum(
            float(metric["at_risk"])
            for metric in financials
        )

        with SessionLocal() as session:
            repository = AnalyticsRepository(
                session
            )

            summary = repository.get_run_summary(
                UUID(run_id)
            )

        print(
            "  Sum at_risk across root causes: "
            f"{sum_at_risk:.2f} "
            f"vs total_at_risk "
            f"{summary.total_at_risk:.2f}"
        )

        assert (
            abs(
                sum_at_risk
                - summary.total_at_risk
            )
            < 0.01
        )

    print("ROOT CAUSE PASS")


def verify_batch_runs() -> None:
    print()
    print(
        "=== BATCH RUNS: "
        "multiple runs independent metrics ==="
    )

    metrics = get_run_metrics()

    print(
        f"Total run metrics returned: "
        f"{len(metrics)}"
    )

    for metric in metrics:
        print(
            f"  {str(metric['run_id'])[:8]} "
            f"status={metric['status']} "
            f"payments={metric['total_payments']} "
            f"rate={float(metric['recovery_rate']):.2%}"
        )

    run_ids = {
        str(metric["run_id"])
        for metric in metrics
    }

    assert len(run_ids) == len(metrics)

    if len(metrics) >= 2:
        assert (
            metrics[0]["run_id"]
            != metrics[1]["run_id"]
        )

        print(
            "  -> Each run independent PASS"
        )

    print("BATCH RUNS PASS")


def verify_case_explorer(
    run_id: str,
) -> None:
    print()
    print(
        "=== CASE EXPLORER: "
        "deep integrity check ==="
    )

    cases = get_cases(run_id)

    print(
        f"Cases for latest run: "
        f"{len(cases)}"
    )

    if not cases:
        raise RuntimeError(
            "No cases found for latest run."
        )

    random.seed(0)

    sample = random.choice(cases)

    payment_id = str(
        sample["payment_id"]
    )

    print(
        f"Picking payment {payment_id} "
        f"(customer {sample['customer_id']}) "
        f"root_cause={sample['root_cause']} "
        f"diagnosis_source="
        f"{sample['diagnosis_source']}"
    )

    details = get_case_details(
        run_id,
        payment_id,
    )

    assert details is not None

    payment = details["payment"]
    diagnosis = details["diagnosis"]
    recovery_attempts = details[
        "recovery_attempts"
    ]
    audit_events = details[
        "audit_events"
    ]

    print(
        f"Payment: {payment['payment_id']} "
        f"amount {payment['amount']}"
    )

    if diagnosis is not None:
        print(
            f"Diagnosis: {diagnosis}"
        )

        with SessionLocal() as session:
            diagnosis_repository = (
                DiagnosisRepository(session)
            )

            db_diagnosis = (
                diagnosis_repository
                .get_by_run_and_payment(
                    UUID(run_id),
                    UUID(payment_id),
                )
            )

        assert db_diagnosis is not None
        assert (
            str(db_diagnosis.run_id)
            == run_id
        )
        assert (
            str(diagnosis["run_id"])
            == run_id
        )

        print(
            "  -> Diagnosis run_id MATCH"
        )
    else:
        print("  No diagnosis")

    print(
        f"Recovery attempts: "
        f"{len(recovery_attempts)}"
    )

    for attempt in recovery_attempts:
        print(
            f"  attempt "
            f"{attempt['attempt_number']} "
            f"action={attempt['action_type']} "
            f"outcome={attempt['outcome']} "
            f"run_id={attempt['run_id']}"
        )

        assert (
            str(attempt["run_id"])
            == run_id
        )

    print(
        "  -> All recovery run_id MATCH"
    )

    print(
        f"Audit events: "
        f"{len(audit_events)}"
    )

    for event in audit_events:
        print(
            f"  {event['timestamp']} "
            f"{event['event_type']} "
            f"actor={event['actor']} "
            f"decision={event['decision']}"
        )

    with SessionLocal() as session:
        audit_repository = AuditRepository(
            session
        )

        recovery_repository = (
            RecoveryRepository(session)
        )

        db_audits = (
            audit_repository
            .get_for_run_and_payment(
                UUID(run_id),
                UUID(payment_id),
            )
        )

        db_recoveries = (
            recovery_repository
            .get_by_run_and_payment(
                UUID(run_id),
                UUID(payment_id),
            )
        )

        print(
            f"  DB audits count: "
            f"{len(db_audits)} "
            f"DB recs count: "
            f"{len(db_recoveries)}"
        )

        for audit in db_audits:
            assert (
                str(audit.run_id)
                == run_id
            )
            assert (
                str(audit.payment_id)
                == payment_id
            )

        for recovery in db_recoveries:
            assert (
                str(recovery.run_id)
                == run_id
            )
            assert (
                str(recovery.payment_id)
                == payment_id
            )

    print(
        "  -> DB audit/recovery run_id MATCH"
    )

    policy_events = [
        event
        for event in audit_events
        if event["event_type"]
        == "policy_decision"
    ]

    print(
        f"Policy events in audit trail: "
        f"{len(policy_events)}"
    )

    assert policy_events

    print(
        "  -> Policy audit run_id MATCH"
    )

    print("CASE EXPLORER PASS")


def main() -> None:
    run_id = verify_overview()

    verify_root_cause(
        run_id
    )

    verify_batch_runs()

    verify_case_explorer(
        run_id
    )

    print()
    print(
        "=============================================="
    )
    print(
        "          ALL INTEGRITY CHECKS PASSED"
    )
    print(
        "=============================================="
    )


if __name__ == "__main__":
    main()