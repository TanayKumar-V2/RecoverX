from __future__ import annotations

import random
from datetime import datetime, timezone

from app.domain.enums import (
    RecommendedAction,
    RecoveryOutcome,
    RootCause,
)
from app.domain.models import (
    Diagnosis,
    Payment,
    PolicyDecision,
    RecoveryAttempt,
)


RECOVERY_PROBABILITY: dict[RootCause, float] = {
    RootCause.INSUFFICIENT_FUNDS: 0.55,
    RootCause.EXPIRED_CARD: 0.70,
    RootCause.HARD_DECLINE: 0.10,
    RootCause.SOFT_DECLINE: 0.45,
    RootCause.FRAUD_FLAG: 0.0,
    RootCause.TRANSIENT_GLITCH: 0.85,
}

MAX_PROBABILITY = 0.95


class RecoverySimulator:
    def __init__(
        self,
        rng: random.Random | None = None,
    ) -> None:
        self.rng = rng or random.Random()

    def _get_probability(
        self,
        diagnosis: Diagnosis,
        attempt_number: int,
    ) -> float:
        base_probability = RECOVERY_PROBABILITY.get(
            diagnosis.root_cause,
            0.0,
        )

        # Each additional retry becomes slightly less effective.
        retry_penalty = max(attempt_number - 1, 0) * 0.10

        probability = base_probability - retry_penalty

        return max(
            0.0,
            min(probability, MAX_PROBABILITY),
        )

    def execute(
        self,
        payment: Payment,
        diagnosis: Diagnosis,
        decision: PolicyDecision,
    ) -> RecoveryAttempt:

        # Policy rejected the action.
        if not decision.allowed:
            return RecoveryAttempt(
                payment_id=payment.payment_id,
                action_type=RecommendedAction.STOP_NO_ACTION,
                attempt_number=max(
                    decision.attempt_number,
                    1,
                ),
                outcome=RecoveryOutcome.PENDING,
                amount_recovered=0.0,
                timestamp=datetime.now(timezone.utc),
                policy_reason=decision.reason,
            )

        probability = self._get_probability(
            diagnosis,
            decision.attempt_number,
        )

        recovered = self.rng.random() < probability

        outcome = RecoveryOutcome.RECOVERED if recovered else RecoveryOutcome.FAILED

        amount_recovered = payment.amount if recovered else 0.0

        return RecoveryAttempt(
            payment_id=payment.payment_id,
            action_type=decision.action,
            attempt_number=decision.attempt_number,
            outcome=outcome,
            amount_recovered=amount_recovered,
            timestamp=datetime.now(timezone.utc),
            policy_reason=decision.reason,
        )

    def execute_batch(
        self,
        cases: list[tuple[Payment, Diagnosis, PolicyDecision]],
    ) -> list[RecoveryAttempt]:

        return [
            self.execute(
                payment,
                diagnosis,
                decision,
            )
            for payment, diagnosis, decision in cases
        ]
