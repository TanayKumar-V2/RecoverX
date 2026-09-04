from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.enums import AuditEventType
from app.domain.models import Payment
from app.repositories.analytics_repository import (
    AnalyticsRepository,
    CaseSummary,
    RootCauseFinancialMetric,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.orm_models import (
    Base,
    RecoveryAttemptORM,
)
from app.repositories.payment_repository import PaymentRepository


def test_run_summary_only_uses_requested_run() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run_id = uuid4()
        other_run_id = uuid4()

        payment_one = Payment(
            payment_id=uuid4(),
            customer_id="CUST-1",
            amount=1000.0,
            currency="INR",
            decline_code="network_error",
            customer_tenure_months=12,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_two = Payment(
            payment_id=uuid4(),
            customer_id="CUST-2",
            amount=2000.0,
            currency="INR",
            decline_code="expired_card",
            customer_tenure_months=24,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_repository = PaymentRepository(
            session
        )

        payment_repository.save(payment_one)
        payment_repository.save(payment_two)

        audit_repository = AuditRepository(
            session
        )

        audit_repository.record(
            payment_id=payment_one.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="transient_glitch",
        )

        audit_repository.record(
            payment_id=payment_two.payment_id,
            run_id=other_run_id,
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
                outcome="recovered",
                amount_recovered=1000.0,
                timestamp=datetime.now(UTC),
                policy_reason="policy allows attempt 1/2",
            )
        )

        session.add(
            RecoveryAttemptORM(
                action_id=uuid4(),
                run_id=other_run_id,
                payment_id=payment_two.payment_id,
                action_type="send_update_link",
                attempt_number=1,
                outcome="recovered",
                amount_recovered=2000.0,
                timestamp=datetime.now(UTC),
                policy_reason="policy allows attempt 1/1",
            )
        )

        session.commit()

        analytics = AnalyticsRepository(
            session
        )

        summary = analytics.get_run_summary(
            run_id
        )

        assert summary.total_payments == 1
        assert summary.total_at_risk == 1000.0
        assert summary.total_recovered == 1000.0
        assert summary.recovery_rate == 1.0
        assert summary.successful_recoveries == 1
        assert summary.failed_recoveries == 0
        assert summary.pending_recoveries == 0

        root_causes = (
            analytics.get_root_cause_breakdown(
                run_id
            )
        )

        assert root_causes == {
            "transient_glitch": 1
        }


def test_get_root_cause_financials() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run_id = uuid4()

        payment_one = Payment(
            payment_id=uuid4(),
            customer_id="CUST-1",
            amount=1000.0,
            currency="INR",
            decline_code="network_error",
            customer_tenure_months=12,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_two = Payment(
            payment_id=uuid4(),
            customer_id="CUST-2",
            amount=500.0,
            currency="INR",
            decline_code="network_error",
            customer_tenure_months=6,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_three = Payment(
            payment_id=uuid4(),
            customer_id="CUST-3",
            amount=2000.0,
            currency="INR",
            decline_code="insufficient_funds",
            customer_tenure_months=24,
            past_retry_count=0,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_repository = PaymentRepository(session)
        payment_repository.save(payment_one)
        payment_repository.save(payment_two)
        payment_repository.save(payment_three)

        audit_repository = AuditRepository(session)
        audit_repository.record(
            payment_id=payment_one.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="transient_glitch",
        )
        audit_repository.record(
            payment_id=payment_two.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="transient_glitch",
        )
        audit_repository.record(
            payment_id=payment_three.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="rule",
            decision="insufficient_funds",
        )

        # payment_one has two recovery attempts in this run: 600 + 400 = 1000 recovered
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
                policy_reason="first try",
            )
        )
        session.add(
            RecoveryAttemptORM(
                action_id=uuid4(),
                run_id=run_id,
                payment_id=payment_one.payment_id,
                action_type="immediate_retry",
                attempt_number=2,
                outcome="recovered",
                amount_recovered=1000.0,
                timestamp=datetime.now(UTC),
                policy_reason="second try",
            )
        )

        # payment_two has no recovery attempt (0.0 recovered)

        # payment_three has a recovered attempt of 1000.0 out of 2000.0
        session.add(
            RecoveryAttemptORM(
                action_id=uuid4(),
                run_id=run_id,
                payment_id=payment_three.payment_id,
                action_type="smart_retry_schedule",
                attempt_number=1,
                outcome="recovered",
                amount_recovered=1000.0,
                timestamp=datetime.now(UTC),
                policy_reason="scheduled retry",
            )
        )

        session.commit()

        analytics = AnalyticsRepository(session)
        metrics = analytics.get_root_cause_financials(run_id)

        assert len(metrics) == 2
        # Ordered by at_risk descending: insufficient_funds (2000) then transient_glitch (1500)
        assert metrics[0] == RootCauseFinancialMetric(
            root_cause="insufficient_funds",
            payments=1,
            at_risk=2000.0,
            recovered=1000.0,
            recovery_rate=0.5,
        )
        assert metrics[1] == RootCauseFinancialMetric(
            root_cause="transient_glitch",
            payments=2,
            at_risk=1500.0,
            recovered=1000.0,
            recovery_rate=1000.0 / 1500.0,
        )


def test_get_cases_for_run() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run_id = uuid4()

        payment = Payment(
            payment_id=uuid4(),
            customer_id="CUST-1",
            amount=1250.0,
            currency="INR",
            decline_code="insufficient_funds",
            customer_tenure_months=12,
            past_retry_count=1,
            failed_at=datetime.now(UTC),
            subscription_plan="monthly",
        )

        payment_repo = PaymentRepository(session)
        payment_repo.save(payment)

        audit_repo = AuditRepository(session)
        audit_repo.record(
            payment_id=payment.payment_id,
            run_id=run_id,
            event_type=AuditEventType.DIAGNOSIS,
            actor="llm",
            decision="insufficient_funds",
            metadata={"confidence": 0.95},
        )
        audit_repo.record(
            payment_id=payment.payment_id,
            run_id=run_id,
            event_type=AuditEventType.POLICY_DECISION,
            actor="rule",
            decision="smart_retry_schedule",
        )

        session.add(
            RecoveryAttemptORM(
                action_id=uuid4(),
                run_id=run_id,
                payment_id=payment.payment_id,
                action_type="smart_retry_schedule",
                attempt_number=1,
                outcome="recovered",
                amount_recovered=1250.0,
                timestamp=datetime.now(UTC),
                policy_reason="schedule retry for pay day",
            )
        )
        session.commit()

        analytics = AnalyticsRepository(session)
        cases = analytics.get_cases_for_run(run_id)

        assert len(cases) == 1
        assert cases[0] == CaseSummary(
            payment_id=payment.payment_id,
            customer_id="CUST-1",
            amount=1250.0,
            decline_code="insufficient_funds",
            root_cause="insufficient_funds",
            diagnosis_source="llm",
            confidence=0.95,
            action="smart_retry_schedule",
            outcome="recovered",
            amount_recovered=1250.0,
        )