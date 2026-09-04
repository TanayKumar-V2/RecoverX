from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.enums import AuditEventType
from app.domain.models import Payment
from app.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.orm_models import (
    Base,
    RecoveryAttemptORM,
)
from app.repositories.payment_repository import PaymentRepository


def test_root_cause_insights_identify_financial_extremes() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False
        },
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run_id = uuid4()

        payment_one = Payment(
            payment_id=uuid4(),
            customer_id="CUST-1",
            amount=10000.0,
            currency="INR",
            decline_code="network_error",
            customer_tenure_months=24,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_two = Payment(
            payment_id=uuid4(),
            customer_id="CUST-2",
            amount=5000.0,
            currency="INR",
            decline_code="expired_card",
            customer_tenure_months=12,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_repository = PaymentRepository(
            session
        )

        payment_repository.save(
            payment_one
        )

        payment_repository.save(
            payment_two
        )

        audit = AuditRepository(
            session
        )

        audit.record(
            payment_id=payment_one.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="transient_glitch",
        )

        audit.record(
            payment_id=payment_two.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="expired_card",
        )

        session.add(
            RecoveryAttemptORM(
                action_id=uuid4(),
                run_id=run_id,
                payment_id=payment_one.payment_id,
                action_type="immediate_retry",
                attempt_number=1,
                outcome="failed",
                amount_recovered=0.0,
                timestamp=datetime.now(UTC),
                policy_reason="test",
            )
        )

        session.add(
            RecoveryAttemptORM(
                action_id=uuid4(),
                run_id=run_id,
                payment_id=payment_two.payment_id,
                action_type="send_update_link",
                attempt_number=1,
                outcome="recovered",
                amount_recovered=5000.0,
                timestamp=datetime.now(UTC),
                policy_reason="test",
            )
        )

        session.commit()

        repository = AnalyticsRepository(
            session
        )

        insights = (
            repository.get_root_cause_insights(
                run_id
            )
        )

        assert len(insights) == 3

        assert (
            insights[0].root_cause
            == "transient_glitch"
        )

        assert insights[0].value == 10000.0

        assert (
            insights[1].root_cause
            == "expired_card"
        )

        assert insights[1].value == 1.0

        assert (
            insights[2].root_cause
            == "transient_glitch"
        )

        assert insights[2].value == 10000.0