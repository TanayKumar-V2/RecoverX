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


def test_root_cause_financials_are_run_scoped() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run_id = uuid4()
        other_run_id = uuid4()

        payment = Payment(
            payment_id=uuid4(),
            customer_id="CUST-1",
            amount=5000.0,
            currency="INR",
            decline_code="network_error",
            customer_tenure_months=24,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        PaymentRepository(session).save(
            payment
        )

        audit = AuditRepository(session)

        audit.record(
            payment_id=payment.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="transient_glitch",
        )

        audit.record(
            payment_id=payment.payment_id,
            run_id=other_run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="expired_card",
        )

        session.add(
            RecoveryAttemptORM(
                action_id=uuid4(),
                run_id=run_id,
                payment_id=payment.payment_id,
                action_type="immediate_retry",
                attempt_number=1,
                outcome="recovered",
                amount_recovered=4000.0,
                timestamp=datetime.now(UTC),
                policy_reason="policy allows attempt 1/2",
            )
        )

        session.commit()

        analytics = AnalyticsRepository(
            session
        )

        results = (
            analytics.get_root_cause_financials(
                run_id
            )
        )

        assert len(results) == 1

        metric = results[0]

        assert metric.root_cause == (
            "transient_glitch"
        )
        assert metric.payments == 1
        assert metric.at_risk == 5000.0
        assert metric.recovered == 4000.0
        assert metric.recovery_rate == 0.8