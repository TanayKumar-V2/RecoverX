from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.repositories.orm_models import (
    AuditEventORM,
    BatchRunORM,
    PaymentORM,
    RecoveryAttemptORM,
)


@dataclass(frozen=True, slots=True)
class RunSummary:
    run_id: UUID
    total_payments: int
    total_at_risk: float
    total_recovered: float
    recovery_rate: float
    successful_recoveries: int
    failed_recoveries: int
    pending_recoveries: int


@dataclass(frozen=True, slots=True)
class RootCauseFinancialMetric:
    root_cause: str
    payments: int
    at_risk: float
    recovered: float
    recovery_rate: float

@dataclass(frozen=True, slots=True)
class RootCauseInsight:
    label: str
    root_cause: str
    value: float
    
@dataclass(frozen=True, slots=True)
class CaseSummary:
    payment_id: UUID
    customer_id: str
    amount: float
    decline_code: str
    root_cause: str | None
    diagnosis_source: str | None
    confidence: float | None
    action: str | None
    outcome: str | None
    amount_recovered: float

@dataclass(frozen=True, slots=True)
class RunMetrics:
    run_id: UUID
    started_at: object
    completed_at: object | None
    status: str
    total_payments: int
    total_at_risk: float
    total_recovered: float
    recovery_rate: float

class AnalyticsRepository:
    """Read-only queries used by reporting and dashboard layers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_run_summary(
        self,
        run_id: UUID,
    ) -> RunSummary:
        payment_count_statement = select(
            func.count(
                distinct(RecoveryAttemptORM.payment_id)
            )
        ).where(
            RecoveryAttemptORM.run_id == run_id
        )

        total_payments = (
            self.session.scalar(
                payment_count_statement
            )
            or 0
        )

        at_risk_statement = select(
            func.coalesce(
                func.sum(PaymentORM.amount),
                0.0,
            )
        ).where(
            PaymentORM.payment_id.in_(
                select(
                    RecoveryAttemptORM.payment_id
                ).where(
                    RecoveryAttemptORM.run_id == run_id
                )
            )
        )

        total_at_risk = float(
            self.session.scalar(
                at_risk_statement
            )
            or 0.0
        )

        recovered_statement = select(
            func.coalesce(
                func.sum(
                    RecoveryAttemptORM.amount_recovered
                ),
                0.0,
            )
        ).where(
            RecoveryAttemptORM.run_id == run_id
        )

        total_recovered = float(
            self.session.scalar(
                recovered_statement
            )
            or 0.0
        )

        successful_statement = select(
            func.count(RecoveryAttemptORM.action_id)
        ).where(
            RecoveryAttemptORM.run_id == run_id,
            RecoveryAttemptORM.outcome == "recovered",
        )

        successful_recoveries = (
            self.session.scalar(
                successful_statement
            )
            or 0
        )

        failed_statement = select(
            func.count(RecoveryAttemptORM.action_id)
        ).where(
            RecoveryAttemptORM.run_id == run_id,
            RecoveryAttemptORM.outcome == "failed",
        )

        failed_recoveries = (
            self.session.scalar(
                failed_statement
            )
            or 0
        )

        pending_statement = select(
            func.count(RecoveryAttemptORM.action_id)
        ).where(
            RecoveryAttemptORM.run_id == run_id,
            RecoveryAttemptORM.outcome == "pending",
        )

        pending_recoveries = (
            self.session.scalar(
                pending_statement
            )
            or 0
        )

        recovery_rate = (
            total_recovered / total_at_risk
            if total_at_risk > 0
            else 0.0
        )

        return RunSummary(
            run_id=run_id,
            total_payments=int(total_payments),
            total_at_risk=total_at_risk,
            total_recovered=total_recovered,
            recovery_rate=recovery_rate,
            successful_recoveries=int(
                successful_recoveries
            ),
            failed_recoveries=int(
                failed_recoveries
            ),
            pending_recoveries=int(
                pending_recoveries
            ),
        )

    def get_root_cause_breakdown(
        self,
        run_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                AuditEventORM.decision,
                func.count(AuditEventORM.id),
            )
            .where(
                AuditEventORM.run_id == run_id,
                AuditEventORM.event_type == "diagnosis",
                AuditEventORM.decision.is_not(None),
            )
            .group_by(
                AuditEventORM.decision
            )
            .order_by(
                func.count(AuditEventORM.id).desc()
            )
        )

        rows = self.session.execute(
            statement
        ).all()

        return {
            str(decision): int(count)
            for decision, count in rows
            if decision is not None
        }

    def get_action_breakdown(
        self,
        run_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                AuditEventORM.decision,
                func.count(AuditEventORM.id),
            )
            .where(
                AuditEventORM.run_id == run_id,
                AuditEventORM.event_type
                == "policy_decision",
                AuditEventORM.decision.is_not(None),
            )
            .group_by(
                AuditEventORM.decision
            )
            .order_by(
                func.count(AuditEventORM.id).desc()
            )
        )

        rows = self.session.execute(
            statement
        ).all()

        return {
            str(decision): int(count)
            for decision, count in rows
            if decision is not None
        }

    def get_recovery_outcome_breakdown(
        self,
        run_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                RecoveryAttemptORM.outcome,
                func.count(
                    RecoveryAttemptORM.action_id
                ),
            )
            .where(
                RecoveryAttemptORM.run_id == run_id
            )
            .group_by(
                RecoveryAttemptORM.outcome
            )
            .order_by(
                func.count(
                    RecoveryAttemptORM.action_id
                ).desc()
            )
        )

        rows = self.session.execute(
            statement
        ).all()

        return {
            str(outcome): int(count)
            for outcome, count in rows
        }

    def get_root_cause_financials(
        self,
        run_id: UUID,
    ) -> list[RootCauseFinancialMetric]:
        recovery_per_payment = (
            select(
                RecoveryAttemptORM.payment_id.label(
                    "payment_id"
                ),
                func.sum(
                    RecoveryAttemptORM.amount_recovered
                ).label(
                    "recovered"
                ),
            )
            .where(
                RecoveryAttemptORM.run_id == run_id
            )
            .group_by(
                RecoveryAttemptORM.payment_id
            )
            .subquery()
        )

        statement = (
            select(
                AuditEventORM.decision,
                func.count(
                    distinct(AuditEventORM.payment_id)
                ).label("payments"),
                func.sum(
                    PaymentORM.amount
                ).label("at_risk"),
                func.coalesce(
                    func.sum(
                        recovery_per_payment.c.recovered
                    ),
                    0.0,
                ).label("recovered"),
            )
            .join(
                PaymentORM,
                PaymentORM.payment_id
                == AuditEventORM.payment_id,
            )
            .outerjoin(
                recovery_per_payment,
                recovery_per_payment.c.payment_id
                == AuditEventORM.payment_id,
            )
            .where(
                AuditEventORM.run_id == run_id,
                AuditEventORM.event_type == "diagnosis",
                AuditEventORM.decision.is_not(None),
            )
            .group_by(
                AuditEventORM.decision
            )
            .order_by(
                func.sum(
                    PaymentORM.amount
                ).desc()
            )
        )

        rows = self.session.execute(
            statement
        ).all()

        metrics: list[RootCauseFinancialMetric] = []

        for (
            root_cause,
            payments,
            at_risk,
            recovered,
        ) in rows:
            at_risk_value = float(at_risk or 0.0)
            recovered_value = float(recovered or 0.0)

            recovery_rate = (
                recovered_value / at_risk_value
                if at_risk_value > 0
                else 0.0
            )

            metrics.append(
                RootCauseFinancialMetric(
                    root_cause=str(root_cause),
                    payments=int(payments),
                    at_risk=at_risk_value,
                    recovered=recovered_value,
                    recovery_rate=recovery_rate,
                )
            )

        return metrics

    def get_cases_for_run(
        self,
        run_id: UUID,
    ) -> list[CaseSummary]:
        latest_recovery = (
            select(
                RecoveryAttemptORM.payment_id.label(
                    "payment_id"
                ),
                RecoveryAttemptORM.outcome.label(
                    "outcome"
                ),
                RecoveryAttemptORM.amount_recovered.label(
                    "amount_recovered"
                ),
            )
            .where(
                RecoveryAttemptORM.run_id == run_id
            )
            .subquery()
        )

        diagnosis = (
            select(
                AuditEventORM.payment_id.label(
                    "payment_id"
                ),
                AuditEventORM.decision.label(
                    "root_cause"
                ),
                AuditEventORM.actor.label(
                    "diagnosis_source"
                ),
                AuditEventORM.metadata_json.label(
                    "metadata"
                ),
            )
            .where(
                AuditEventORM.run_id == run_id,
                AuditEventORM.event_type == "diagnosis",
            )
            .subquery()
        )

        policy = (
            select(
                AuditEventORM.payment_id.label(
                    "payment_id"
                ),
                AuditEventORM.decision.label(
                    "action"
                ),
            )
            .where(
                AuditEventORM.run_id == run_id,
                AuditEventORM.event_type
                == "policy_decision",
            )
            .subquery()
        )

        statement = (
            select(
                PaymentORM.payment_id,
                PaymentORM.customer_id,
                PaymentORM.amount,
                PaymentORM.decline_code,
                diagnosis.c.root_cause,
                diagnosis.c.diagnosis_source,
                diagnosis.c.metadata,
                policy.c.action,
                latest_recovery.c.outcome,
                latest_recovery.c.amount_recovered,
            )
            .join(
                diagnosis,
                diagnosis.c.payment_id
                == PaymentORM.payment_id,
            )
            .join(
                policy,
                policy.c.payment_id
                == PaymentORM.payment_id,
            )
            .outerjoin(
                latest_recovery,
                latest_recovery.c.payment_id
                == PaymentORM.payment_id,
            )
            .order_by(
                PaymentORM.amount.desc()
            )
        )

        rows = self.session.execute(
            statement
        ).all()

        results: list[CaseSummary] = []

        for row in rows:
            metadata = row.metadata or {}

            confidence = metadata.get(
                "confidence"
            )

            results.append(
                CaseSummary(
                    payment_id=row.payment_id,
                    customer_id=row.customer_id,
                    amount=float(row.amount),
                    decline_code=row.decline_code,
                    root_cause=(
                        str(row.root_cause)
                        if row.root_cause is not None
                        else None
                    ),
                    diagnosis_source=(
                        str(row.diagnosis_source)
                        if row.diagnosis_source is not None
                        else None
                    ),
                    confidence=(
                        float(confidence)
                        if confidence is not None
                        else None
                    ),
                    action=(
                        str(row.action)
                        if row.action is not None
                        else None
                    ),
                    outcome=(
                        str(row.outcome)
                        if row.outcome is not None
                        else None
                    ),
                    amount_recovered=float(
                        row.amount_recovered or 0.0
                    ),
                )
            )

        return results

    def get_all_run_metrics(self) -> list[RunMetrics]:
        run_statement = (
            select(
                BatchRunORM.run_id,
                BatchRunORM.started_at,
                BatchRunORM.completed_at,
                BatchRunORM.status,
            )
            .order_by(
                BatchRunORM.started_at.desc()
            )
        )

        runs = self.session.execute(
            run_statement
        ).all()

        results: list[RunMetrics] = []

        for run in runs:
            payment_ids = select(
                RecoveryAttemptORM.payment_id
            ).where(
                RecoveryAttemptORM.run_id
                == run.run_id
            )

            total_payments = int(
                self.session.scalar(
                    select(
                        func.count(
                            distinct(
                                RecoveryAttemptORM.payment_id
                            )
                        )
                    ).where(
                        RecoveryAttemptORM.run_id
                        == run.run_id
                    )
                )
                or 0
            )

            total_at_risk = float(
                self.session.scalar(
                    select(
                        func.coalesce(
                            func.sum(
                                PaymentORM.amount
                            ),
                            0.0,
                        )
                    ).where(
                        PaymentORM.payment_id.in_(
                            payment_ids
                        )
                    )
                )
                or 0.0
            )

            total_recovered = float(
                self.session.scalar(
                    select(
                        func.coalesce(
                            func.sum(
                                RecoveryAttemptORM.amount_recovered
                            ),
                            0.0,
                        )
                    ).where(
                        RecoveryAttemptORM.run_id
                        == run.run_id
                    )
                )
                or 0.0
            )

            recovery_rate = (
                total_recovered / total_at_risk
                if total_at_risk > 0
                else 0.0
            )

            results.append(
                RunMetrics(
                    run_id=run.run_id,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    status=run.status,
                    total_payments=total_payments,
                    total_at_risk=total_at_risk,
                    total_recovered=total_recovered,
                    recovery_rate=recovery_rate,
                )
            )

        return results

    def get_root_cause_insights(
        self,
        run_id: UUID,
    ) -> list[RootCauseInsight]:
        metrics = self.get_root_cause_financials(
            run_id
        )

        if not metrics:
            return []

        largest_exposure = max(
            metrics,
            key=lambda metric: metric.at_risk,
        )

        best_recovery = max(
            metrics,
            key=lambda metric: metric.recovery_rate,
        )

        largest_unrecovered = max(
            metrics,
            key=lambda metric: (
                metric.at_risk - metric.recovered
            ),
        )

        return [
            RootCauseInsight(
                label="Largest revenue exposure",
                root_cause=largest_exposure.root_cause,
                value=largest_exposure.at_risk,
            ),
            RootCauseInsight(
                label="Best recovery rate",
                root_cause=best_recovery.root_cause,
                value=best_recovery.recovery_rate,
            ),
            RootCauseInsight(
                label="Largest unrecovered opportunity",
                root_cause=largest_unrecovered.root_cause,
                value=(
                    largest_unrecovered.at_risk
                    - largest_unrecovered.recovered
                ),
            ),
        ]