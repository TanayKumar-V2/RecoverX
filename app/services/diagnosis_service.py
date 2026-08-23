from app.ai.classifier import CohereClassifier
from app.domain.enums import DiagnosisSource, RecommendedAction, RootCause
from app.domain.models import Diagnosis, Payment


RULE_TABLE: dict[str, tuple[RootCause, RecommendedAction]] = {
    "expired_card": (
        RootCause.EXPIRED_CARD,
        RecommendedAction.SEND_UPDATE_LINK,
    ),
    "insufficient_funds": (
        RootCause.INSUFFICIENT_FUNDS,
        RecommendedAction.SMART_RETRY,
    ),
    "network_error": (
        RootCause.TRANSIENT_GLITCH,
        RecommendedAction.IMMEDIATE_RETRY,
    ),
    "fraud_suspected": (
        RootCause.FRAUD_FLAG,
        RecommendedAction.ESCALATE_MANUAL_REVIEW,
    ),
}


def classify_by_rule(
    payment: Payment,
) -> Diagnosis | None:

    result = RULE_TABLE.get(payment.decline_code)

    if result is None:
        return None

    root_cause, action = result

    return Diagnosis(
        payment_id=payment.payment_id,
        root_cause=root_cause,
        confidence=1.0,
        source=DiagnosisSource.RULE,
        recommended_action=action,
        reasoning=(f"Deterministic mapping for decline code '{payment.decline_code}'."),
    )


class DiagnosisService:
    def __init__(
        self,
        classifier: CohereClassifier | None = None,
    ) -> None:
        self.classifier = classifier or CohereClassifier()

    def diagnose(
        self,
        payment: Payment,
    ) -> Diagnosis:

        rule_diagnosis = classify_by_rule(payment)

        if rule_diagnosis is not None:
            return rule_diagnosis

        return self.classifier.classify(payment)
