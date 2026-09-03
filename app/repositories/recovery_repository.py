from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import RecommendedAction, RecoveryOutcome
from app.domain.models import RecoveryAttempt
from app.repositories.orm_models import RecoveryAttemptORM


class RecoveryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, attempt: RecoveryAttempt) -> None:
        row = RecoveryAttemptORM(
            action_id=attempt.action_id,
            payment_id=attempt.payment_id,
            action_type=attempt.action_type.value,
            attempt_number=attempt.attempt_number,
            outcome=attempt.outcome.value,
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
            .where(RecoveryAttemptORM.payment_id == payment_id)
            .order_by(RecoveryAttemptORM.attempt_number)
        )

        rows = self.session.scalars(statement).all()

        return [
            RecoveryAttempt(
                action_id=row.action_id,
                payment_id=row.payment_id,
                action_type=RecommendedAction(row.action_type),
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
                payment_id=row.payment_id,
                action_type=RecommendedAction(row.action_type),
                attempt_number=row.attempt_number,
                outcome=RecoveryOutcome(row.outcome),
                amount_recovered=row.amount_recovered,
                timestamp=row.timestamp,
                policy_reason=row.policy_reason,
            )
            for row in rows
        ]