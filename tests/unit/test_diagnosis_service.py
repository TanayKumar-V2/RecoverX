from datetime import datetime, timezone
from uuid import uuid4

from app.domain.enums import (
    DiagnosisSource,
    RecommendedAction,
    RootCause,
)
from app.domain.models import Diagnosis, Payment
from app.services.diagnosis_service import (
    DiagnosisService,
    classify_by_rule,
)


def create_payment(
    decline_code: str,
) -> Payment:
    return Payment(
        payment_id=uuid4(),
        customer_id="CUST-12345",
        amount=1499.00,
        currency="INR",
        decline_code=decline_code,
        customer_tenure_months=18,
        past_retry_count=0,
        failed_at=datetime.now(timezone.utc),
        subscription_plan="monthly",
    )


def test_known_decline_uses_rule_engine() -> None:
    payment = create_payment("expired_card")

    diagnosis = classify_by_rule(payment)

    assert diagnosis is not None
    assert diagnosis.source == DiagnosisSource.RULE
    assert diagnosis.root_cause == RootCause.EXPIRED_CARD
    assert diagnosis.recommended_action == RecommendedAction.SEND_UPDATE_LINK
    assert diagnosis.confidence == 1.0


def test_unknown_decline_is_not_rule_classified() -> None:
    payment = create_payment("do_not_honor")

    diagnosis = classify_by_rule(payment)

    assert diagnosis is None
