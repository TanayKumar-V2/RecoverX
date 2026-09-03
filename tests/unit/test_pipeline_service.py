from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.classifier import CohereClassifier
from app.domain.enums import (
    AuditEventType,
    DiagnosisSource,
    RecommendedAction,
    RootCause,
)
from app.domain.models import Diagnosis, Payment
from app.repositories.audit_repository import AuditRepository
from app.repositories.batch_run_repository import BatchRunRepository
from app.repositories.diagnosis_repository import DiagnosisRepository
from app.repositories.orm_models import AuditEventORM, Base
from app.repositories.payment_repository import PaymentRepository
from app.repositories.recovery_repository import RecoveryRepository
from app.services.diagnosis_service import DiagnosisService
from app.services.pipeline_service import PipelineService
from app.services.recovery_service import RecoverySimulator


class StubCohereClassifier(CohereClassifier):
    def __init__(self) -> None:
        pass

    def classify(
        self,
        payment: Payment,
    ) -> Diagnosis:
        return Diagnosis(
            payment_id=payment.payment_id,
            root_cause=RootCause.HARD_DECLINE,
            confidence=0.90,
            source=DiagnosisSource.LLM,
            recommended_action=RecommendedAction.STOP_NO_ACTION,
            reasoning="Ambiguous decline requires a conservative action.",
        )


def make_payment(
    decline_code: str,
    amount: float,
) -> Payment:
    return Payment(
        payment_id=uuid4(),
        customer_id=f"CUST-{uuid4().hex[:8]}",
        amount=amount,
        currency="INR",
        decline_code=decline_code,
        customer_tenure_months=24,
        past_retry_count=0,
        failed_at=datetime.now(UTC),
        subscription_plan="monthly",
    )


def build_pipeline(
    session: Session,
) -> PipelineService:
    diagnosis_service = DiagnosisService(
        classifier=cast(
            CohereClassifier,
            StubCohereClassifier(),
        )
    )

    recovery_service = RecoverySimulator(
        rng=random.Random(42),
    )

    return PipelineService(
        diagnosis_service=diagnosis_service,
        recovery_service=recovery_service,
        payment_repository=PaymentRepository(session),
        diagnosis_repository=DiagnosisRepository(session),
        recovery_repository=RecoveryRepository(session),
        audit_repository=AuditRepository(session),
        batch_run_repository=BatchRunRepository(session),
    )


def test_pipeline_processes_batch_and_persists_audit_trail() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        pipeline = build_pipeline(session)

        payments = [
            make_payment(
                decline_code="network_error",
                amount=1000.0,
            ),
            make_payment(
                decline_code="expired_card",
                amount=2000.0,
            ),
            make_payment(
                decline_code="do_not_honor",
                amount=3000.0,
            ),
        ]

        result = pipeline.run_batch(payments)

        assert result.total_payments == 3
        assert result.total_at_risk == 6000.0
        assert result.total_recovered >= 0.0
        assert 0.0 <= result.recovery_rate <= 1.0

        assert result.rule_diagnoses == 2
        assert result.llm_diagnoses == 1

        audit_events = session.scalars(
            select(AuditEventORM)
        ).all()

        assert len(audit_events) == 9

        event_types = [
            event.event_type
            for event in audit_events
        ]

        assert event_types.count(
            AuditEventType.DIAGNOSIS.value
        ) == 3

        assert event_types.count(
            AuditEventType.POLICY_DECISION.value
        ) == 3

        assert event_types.count(
            AuditEventType.RECOVERY_ATTEMPT.value
        ) == 3