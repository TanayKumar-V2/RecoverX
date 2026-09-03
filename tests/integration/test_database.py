from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain.enums import (
    AuditEventType,
    DiagnosisSource,
    RecommendedAction,
    RootCause,
)
from app.domain.models import Diagnosis, Payment
from app.repositories.audit_repository import AuditRepository
from app.repositories.orm_models import AuditEventORM, Base, PaymentORM
from app.repositories.payment_repository import PaymentRepository


def test_payment_and_audit_are_persisted() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        payment = Payment(
            payment_id=uuid4(),
            customer_id="CUST-TEST",
            amount=2499.0,
            currency="INR",
            decline_code="network_error",
            customer_tenure_months=24,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_repository = PaymentRepository(session)
        payment_repository.save(payment)

        diagnosis = Diagnosis(
            payment_id=payment.payment_id,
            root_cause=RootCause.TRANSIENT_GLITCH,
            confidence=1.0,
            source=DiagnosisSource.RULE,
            recommended_action=RecommendedAction.IMMEDIATE_RETRY,
            reasoning="Network error is transient.",
        )

        audit_repository = AuditRepository(session)

        audit_repository.record(
            payment_id=payment.payment_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule_engine",
            decision=diagnosis.root_cause,
            metadata={
                "confidence": diagnosis.confidence,
            },
        )

        session.commit()

        stored_payment = session.get(
            PaymentORM,
            payment.payment_id,
        )

        assert stored_payment is not None
        assert stored_payment.customer_id == "CUST-TEST"
        assert stored_payment.amount == 2499.0
        assert stored_payment.decline_code == "network_error"

        events = session.scalars(
            select(AuditEventORM)
        ).all()

        assert len(events) == 1

        event = events[0]

        assert event.payment_id == payment.payment_id
        assert event.event_type == "diagnosis"
        assert event.actor == "rule_engine"
        assert event.decision == "transient_glitch"
        assert event.metadata_json == {
            "confidence": 1.0,
        }