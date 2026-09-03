from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import AuditEventType
from app.repositories.orm_models import AuditEventORM


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        payment_id: UUID,
        event_type: AuditEventType,
        actor: str,
        decision: str | None = None,
        policy_reason: str | None = None,
        metadata: dict[str, object] | None = None,
        run_id: UUID | None = None,
    ) -> None:
        event = AuditEventORM(
            run_id=run_id,
            payment_id=payment_id,
            event_type=event_type.value,
            actor=actor,
            decision=decision,
            policy_reason=policy_reason,
            metadata_json=metadata or {},
        )

        self.session.add(event)
        self.session.flush()

    def get_for_payment(
        self,
        payment_id: UUID,
    ) -> list[AuditEventORM]:
        statement = (
            select(AuditEventORM)
            .where(
                AuditEventORM.payment_id == payment_id
            )
            .order_by(
                AuditEventORM.timestamp
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_for_run(
        self,
        run_id: UUID,
    ) -> list[AuditEventORM]:
        statement = (
            select(AuditEventORM)
            .where(
                AuditEventORM.run_id == run_id
            )
            .order_by(
                AuditEventORM.timestamp
            )
        )

        return list(
            self.session.scalars(statement).all()
        )