from __future__ import annotations

import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.enums import RecommendedAction, RecoveryOutcome, RootCause
from app.domain.models import Diagnosis, Payment, PolicyDecision, RecoveryAttempt

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

        retry_penalty = max(
            attempt_number - 1,
            0,
        ) * 0.10

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
        run_id: UUID | None = None,
    ) -> RecoveryAttempt:
        actual_run_id = run_id if run_id is not None else uuid4()

        if not decision.allowed:
            return RecoveryAttempt(
                run_id=actual_run_id,
                payment_id=payment.payment_id,
                action_type=RecommendedAction.STOP_NO_ACTION,
                attempt_number=max(
                    decision.attempt_number,
                    1,
                ),
                outcome=RecoveryOutcome.PENDING,
                amount_recovered=0.0,
                timestamp=datetime.now(UTC),
                policy_reason=decision.reason,
            )

        probability = self._get_probability(
            diagnosis,
            decision.attempt_number,
        )

        recovered = self.rng.random() < probability

        outcome = (
            RecoveryOutcome.RECOVERED
            if recovered
            else RecoveryOutcome.FAILED
        )

        amount_recovered = (
            payment.amount
            if recovered
            else 0.0
        )

        return RecoveryAttempt(
            run_id=actual_run_id,
            payment_id=payment.payment_id,
            action_type=decision.action,
            attempt_number=max(decision.attempt_number, 1),
            outcome=outcome,
            amount_recovered=amount_recovered,
            timestamp=datetime.now(UTC),
            policy_reason=decision.reason,
        )

    def execute_batch(
        self,
        cases: list[
            tuple[
                Payment,
                Diagnosis,
                PolicyDecision,
            ]
        ],
        run_id: UUID | None = None,
    ) -> list[RecoveryAttempt]:
        actual_run_id = run_id if run_id is not None else uuid4()
        return [
            self.execute(
                payment,
                diagnosis,
                decision,
                actual_run_id,
            )
            for payment, diagnosis, decision in cases
        ]