from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.repositories.orm_models import (
    AuditEventORM,
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