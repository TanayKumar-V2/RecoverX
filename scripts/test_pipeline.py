import random
from datetime import UTC, datetime

from app.domain.enums import (
    DiagnosisSource,
    RecommendedAction,
    RootCause,
)
from app.domain.models import Diagnosis, Payment
from app.services.policy_service import decide_action
from app.services.recovery_service import RecoverySimulator


def main() -> None:
    payment = Payment(
        customer_id="CUST-DEMO",
        amount=2499.0,
        currency="INR",
        decline_code="network_error",
        customer_tenure_months=24,
        past_retry_count=0,
        failed_at=datetime.now(UTC),
        subscription_plan="monthly",
    )

    diagnosis = Diagnosis(
        payment_id=payment.payment_id,
        root_cause=RootCause.TRANSIENT_GLITCH,
        confidence=1.0,
        source=DiagnosisSource.RULE,
        recommended_action=(RecommendedAction.IMMEDIATE_RETRY),
        reasoning=("Network errors are treated as transient failures."),
    )

    decision = decide_action(
        payment,
        diagnosis,
    )

    simulator = RecoverySimulator(random.Random(42))

    recovery = simulator.execute(
        payment,
        diagnosis,
        decision,
    )

    print("\n=== REVLOOP CASE ===")

    print("\nPayment:")
    print(payment.model_dump_json(indent=2))

    print("\nDiagnosis:")
    print(diagnosis.model_dump_json(indent=2))

    print("\nPolicy Decision:")
    print(decision.model_dump_json(indent=2))

    print("\nRecovery:")
    print(recovery.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
