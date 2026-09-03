from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import RecommendedAction, RecoveryOutcome
from app.domain.models import RecoveryAttempt
from app.repositories.orm_models import RecoveryAttemptORM


def enum_value(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return str(value.value)

    return value


class RecoveryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, attempt: RecoveryAttempt) -> None:
        row = RecoveryAttemptORM(
            action_id=attempt.action_id,
            run_id=attempt.run_id,
            payment_id=attempt.payment_id,
            action_type=enum_value(attempt.action_type),
            attempt_number=attempt.attempt_number,
            outcome=enum_value(attempt.outcome),
            amount_recovered=attempt.amount_recovered,
            timestamp=attempt.timestamp,
            policy_reason=attempt.policy_reason,
        )

        self.session.add(row)

    def get_by_payment_id(
        self,
        payment_id: UUID,
    ) -> list[RecoveryAttempt]:
        statement = (
            select(RecoveryAttemptORM)
            .where(
                RecoveryAttemptORM.payment_id == payment_id
            )
            .order_by(
                RecoveryAttemptORM.attempt_number
            )
        )

        rows = self.session.scalars(statement).all()

        return [
            RecoveryAttempt(
                action_id=row.action_id,
                run_id=row.run_id
                if row.run_id is not None
                else UUID(int=0),
                payment_id=row.payment_id,
                action_type=RecommendedAction(
                    row.action_type
                ),
                attempt_number=row.attempt_number,
                outcome=RecoveryOutcome(row.outcome),
                amount_recovered=row.amount_recovered,
                timestamp=row.timestamp,
                policy_reason=row.policy_reason,
            )
            for row in rows
        ]

    def get_by_run_id(
        self,
        run_id: UUID,
    ) -> list[RecoveryAttempt]:
        statement = (
            select(RecoveryAttemptORM)
            .where(
                RecoveryAttemptORM.run_id == run_id
            )
            .order_by(
                RecoveryAttemptORM.timestamp
            )
        )

        rows = self.session.scalars(statement).all()

        return [
            RecoveryAttempt(
                action_id=row.action_id,
                run_id=run_id,
                payment_id=row.payment_id,
                action_type=RecommendedAction(
                    row.action_type
                ),
                attempt_number=row.attempt_number,
                outcome=RecoveryOutcome(row.outcome),
                amount_recovered=row.amount_recovered,
                timestamp=row.timestamp,
                policy_reason=row.policy_reason,
            )
            for row in rows
        ]

    def get_by_run_and_payment(
        self,
        run_id: UUID,
        payment_id: UUID,
    ) -> list[RecoveryAttempt]:
        statement = (
            select(RecoveryAttemptORM)
            .where(
                RecoveryAttemptORM.run_id == run_id,
                RecoveryAttemptORM.payment_id == payment_id,
            )
            .order_by(
                RecoveryAttemptORM.attempt_number
            )
        )

        rows = self.session.scalars(statement).all()

        return [
            RecoveryAttempt(
                action_id=row.action_id,
                run_id=run_id,
                payment_id=row.payment_id,
                action_type=RecommendedAction(
                    row.action_type
                ),
                attempt_number=row.attempt_number,
                outcome=RecoveryOutcome(row.outcome),
                amount_recovered=row.amount_recovered,
                timestamp=row.timestamp,
                policy_reason=row.policy_reason,
            )
            for row in rows
        ]

    def list_all(self) -> list[RecoveryAttempt]:
        statement = select(RecoveryAttemptORM).order_by(
            RecoveryAttemptORM.timestamp
        )

        rows = self.session.scalars(statement).all()

        return [
            RecoveryAttempt(
                action_id=row.action_id,
                run_id=row.run_id
                if row.run_id is not None
                else UUID(int=0),
                payment_id=row.payment_id,
                action_type=RecommendedAction(
                    row.action_type
                ),
                attempt_number=row.attempt_number,
                outcome=RecoveryOutcome(row.outcome),
                amount_recovered=row.amount_recovered,
                timestamp=row.timestamp,
                policy_reason=row.policy_reason,
            )
            for row in rows
        ]
        
    