from enum import Enum

from app.domain.enums import RecommendedAction, RootCause
from app.domain.models import Diagnosis, Payment, PolicyDecision
from app.domain.policies import MAX_RETRIES


def enum_value(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return str(value.value)

    return value


def decide_action(
    payment: Payment,
    diagnosis: Diagnosis,
) -> PolicyDecision:

    action = diagnosis.recommended_action

    # Hard safety stop.
    if diagnosis.root_cause == RootCause.FRAUD_FLAG:
        return PolicyDecision(
            payment_id=payment.payment_id,
            action=RecommendedAction.ESCALATE_MANUAL_REVIEW,
            allowed=False,
            reason="hard stop: fraud_flag never auto-retried",
            attempt_number=payment.past_retry_count,
            max_attempts=0,
        )

    # Low-confidence AI decisions require human review.
    if diagnosis.confidence < 0.50:
        return PolicyDecision(
            payment_id=payment.payment_id,
            action=RecommendedAction.ESCALATE_MANUAL_REVIEW,
            allowed=False,
            reason=(
                f"low confidence ({diagnosis.confidence:.2f}); "
                "human review required"
            ),
            attempt_number=payment.past_retry_count,
            max_attempts=0,
        )

    max_attempts = MAX_RETRIES.get(action, 0)

    # No retries allowed for this action.
    if max_attempts == 0:
        return PolicyDecision(
            payment_id=payment.payment_id,
            action=action,
            allowed=True,
            reason=(
                f"policy allows action: "
                f"{enum_value(action)}"
            ),
            attempt_number=payment.past_retry_count,
            max_attempts=0,
        )

    # Maximum retry limit reached.
    if payment.past_retry_count >= max_attempts:
        return PolicyDecision(
            payment_id=payment.payment_id,
            action=RecommendedAction.ESCALATE_MANUAL_REVIEW,
            allowed=False,
            reason=(
                f"stopped: max_retries({max_attempts}) reached; "
                "escalating instead of retrying"
            ),
            attempt_number=payment.past_retry_count,
            max_attempts=max_attempts,
        )

    # Retry is allowed
    
    return PolicyDecision(
        payment_id=payment.payment_id,
        action=action,
        allowed=True,
        reason=(
            f"policy allows attempt "
            f"{payment.past_retry_count + 1}/{max_attempts}"
        ),
        attempt_number=payment.past_retry_count + 1,
        max_attempts=max_attempts,
    )