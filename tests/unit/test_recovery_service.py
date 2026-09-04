import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.enums import (
    DiagnosisSource,
    RecommendedAction,
    RecoveryOutcome,
    RootCause,
)
from app.domain.models import (
    Diagnosis,
    Payment,
    PolicyDecision,
)
from app.services.recovery_service import RecoverySimulator


def create_payment() -> Payment:
    return Payment(
        payment_id=uuid4(),
        customer_id="CUST-123",
        amount=1499.0,
        currency="INR",
        decline_code="network_error",
        customer_tenure_months=18,
        past_retry_count=0,
        failed_at=datetime.now(UTC),
        subscription_plan="monthly",
    )


def create_diagnosis(
    payment: Payment,
    root_cause: RootCause,
    action: RecommendedAction,
    run_id: UUID | None = None,
) -> Diagnosis:
    return Diagnosis(
        run_id=run_id,
        payment_id=payment.payment_id,
        root_cause=root_cause,
        confidence=0.95,
        source=DiagnosisSource.RULE,
        recommended_action=action,
        reasoning="Test diagnosis.",
    )


def create_decision(
    payment: Payment,
    action: RecommendedAction,
    allowed: bool = True,
    attempt_number: int = 1,
    reason: str = "policy allows attempt 1/1",
) -> PolicyDecision:
    return PolicyDecision(
        payment_id=payment.payment_id,
        action=action,
        allowed=allowed,
        reason=reason,
        attempt_number=attempt_number,
        max_attempts=1,
    )


def test_successful_recovery() -> None:
    payment = create_payment()

    diagnosis = create_diagnosis(
        payment,
        RootCause.TRANSIENT_GLITCH,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    decision = create_decision(
        payment,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    # Fixed seed ensures deterministic behavior.
    simulator = RecoverySimulator(random.Random(1))

    result = simulator.execute(
        payment,
        diagnosis,
        decision,
    )

    assert result.outcome == RecoveryOutcome.RECOVERED
    assert result.amount_recovered == payment.amount


def test_failed_recovery() -> None:
    payment = create_payment()

    diagnosis = create_diagnosis(
        payment,
        RootCause.TRANSIENT_GLITCH,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    decision = create_decision(
        payment,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    # Seed chosen to produce a value above 0.85.
    simulator = RecoverySimulator(random.Random(2))

    result = simulator.execute(
        payment,
        diagnosis,
        decision,
    )

    assert result.outcome == RecoveryOutcome.FAILED
    assert result.amount_recovered == 0.0


def test_fraud_never_recovers_automatically() -> None:
    payment = create_payment()

    diagnosis = create_diagnosis(
        payment,
        RootCause.FRAUD_FLAG,
        RecommendedAction.ESCALATE_MANUAL_REVIEW,
    )

    decision = create_decision(
        payment,
        RecommendedAction.ESCALATE_MANUAL_REVIEW,
        allowed=False,
        reason="hard stop: fraud_flag never auto-retried",
    )

    simulator = RecoverySimulator(random.Random(42))

    result = simulator.execute(
        payment,
        diagnosis,
        decision,
    )

    assert result.outcome == RecoveryOutcome.PENDING
    assert result.amount_recovered == 0.0
    assert result.action_type == RecommendedAction.STOP_NO_ACTION


def test_amount_recovered_equals_payment_amount() -> None:
    payment = create_payment()

    diagnosis = create_diagnosis(
        payment,
        RootCause.TRANSIENT_GLITCH,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    decision = create_decision(
        payment,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    simulator = RecoverySimulator(random.Random(1))

    result = simulator.execute(
        payment,
        diagnosis,
        decision,
    )

    if result.outcome == RecoveryOutcome.RECOVERED:
        assert result.amount_recovered == payment.amount
