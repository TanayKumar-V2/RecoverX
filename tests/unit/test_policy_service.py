from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.enums import (
    DiagnosisSource,
    RecommendedAction,
    RootCause,
)
from app.domain.models import Diagnosis, Payment
from app.services.policy_service import decide_action


def create_payment(
    retry_count: int = 0,
) -> Payment:
    return Payment(
        payment_id=uuid4(),
        customer_id="CUST-123",
        amount=1499.0,
        currency="INR",
        decline_code="do_not_honor",
        customer_tenure_months=18,
        past_retry_count=retry_count,
        failed_at=datetime.now(UTC),
        subscription_plan="monthly",
    )


def create_diagnosis(
    payment: Payment,
    root_cause: RootCause,
    action: RecommendedAction,
    confidence: float = 0.95,
    run_id: UUID | None = None,
) -> Diagnosis:
    return Diagnosis(
        run_id=run_id,
        payment_id=payment.payment_id,
        root_cause=root_cause,
        confidence=confidence,
        source=DiagnosisSource.LLM,
        recommended_action=action,
        reasoning="Test diagnosis.",
    )


def test_normal_retry_is_allowed() -> None:
    payment = create_payment(retry_count=0)

    diagnosis = create_diagnosis(
        payment,
        RootCause.INSUFFICIENT_FUNDS,
        RecommendedAction.SMART_RETRY,
    )

    decision = decide_action(payment, diagnosis)

    assert decision.allowed is True
    assert decision.action == RecommendedAction.SMART_RETRY
    assert decision.attempt_number == 1
    assert decision.max_attempts == 3


def test_max_retries_triggers_escalation() -> None:
    payment = create_payment(retry_count=3)

    diagnosis = create_diagnosis(
        payment,
        RootCause.INSUFFICIENT_FUNDS,
        RecommendedAction.SMART_RETRY,
    )

    decision = decide_action(payment, diagnosis)

    assert decision.allowed is False
    assert decision.action == RecommendedAction.ESCALATE_MANUAL_REVIEW
    assert "max_retries" in decision.reason


def test_fraud_is_never_auto_retried() -> None:
    payment = create_payment(retry_count=0)

    diagnosis = create_diagnosis(
        payment,
        RootCause.FRAUD_FLAG,
        RecommendedAction.SMART_RETRY,
    )

    decision = decide_action(payment, diagnosis)

    assert decision.allowed is False
    assert decision.action == RecommendedAction.ESCALATE_MANUAL_REVIEW
    assert "fraud_flag" in decision.reason


def test_low_confidence_triggers_manual_review() -> None:
    payment = create_payment(retry_count=0)

    diagnosis = create_diagnosis(
        payment,
        RootCause.SOFT_DECLINE,
        RecommendedAction.SMART_RETRY,
        confidence=0.31,
    )

    decision = decide_action(payment, diagnosis)

    assert decision.allowed is False
    assert decision.action == RecommendedAction.ESCALATE_MANUAL_REVIEW
    assert "low confidence" in decision.reason


def test_immediate_retry_allows_two_attempts() -> None:
    payment = create_payment(retry_count=1)

    diagnosis = create_diagnosis(
        payment,
        RootCause.TRANSIENT_GLITCH,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    decision = decide_action(payment, diagnosis)

    assert decision.allowed is True
    assert decision.action == RecommendedAction.IMMEDIATE_RETRY
    assert decision.attempt_number == 2
    assert decision.max_attempts == 2


def test_immediate_retry_limit_triggers_escalation() -> None:
    payment = create_payment(retry_count=2)

    diagnosis = create_diagnosis(
        payment,
        RootCause.TRANSIENT_GLITCH,
        RecommendedAction.IMMEDIATE_RETRY,
    )

    decision = decide_action(payment, diagnosis)

    assert decision.allowed is False
    assert decision.action == RecommendedAction.ESCALATE_MANUAL_REVIEW
    assert "max_retries" in decision.reason


def test_update_link_does_not_become_unlimited_retry() -> None:
    payment = create_payment(retry_count=1)

    diagnosis = create_diagnosis(
        payment,
        RootCause.EXPIRED_CARD,
        RecommendedAction.SEND_UPDATE_LINK,
    )

    decision = decide_action(payment, diagnosis)

    assert decision.allowed is False
    assert decision.action == RecommendedAction.ESCALATE_MANUAL_REVIEW
