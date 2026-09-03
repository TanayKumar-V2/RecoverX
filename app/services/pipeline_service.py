from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.enums import (
    AuditEventType,
    DiagnosisSource,
    RecommendedAction,
    RecoveryOutcome,
    RootCause,
)
from app.domain.models import Payment
from app.repositories.audit_repository import AuditRepository
from app.repositories.batch_run_repository import BatchRunRepository
from app.repositories.diagnosis_repository import DiagnosisRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.recovery_repository import RecoveryRepository
from app.services.diagnosis_service import DiagnosisService
from app.services.policy_service import decide_action
from app.services.recovery_service import RecoverySimulator


def enum_value(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return str(value.value)

    return value


@dataclass(frozen=True, slots=True)
class BatchResult:
    run_id: str

    total_payments: int
    total_at_risk: float
    total_recovered: float
    recovery_rate: float

    rule_diagnoses: int
    llm_diagnoses: int

    successful_recoveries: int
    failed_recoveries: int
    pending_recoveries: int

    manual_escalations: int
    fraud_stops: int
    low_confidence_escalations: int
    retry_exhaustions: int


class PipelineService:
    def __init__(
        self,
        diagnosis_service: DiagnosisService,
        recovery_service: RecoverySimulator,
        payment_repository: PaymentRepository,
        diagnosis_repository: DiagnosisRepository,
        recovery_repository: RecoveryRepository,
        audit_repository: AuditRepository,
        batch_run_repository: BatchRunRepository,
    ) -> None:
        self.diagnosis_service = diagnosis_service
        self.recovery_service = recovery_service
        self.payment_repository = payment_repository
        self.diagnosis_repository = diagnosis_repository
        self.recovery_repository = recovery_repository
        self.audit_repository = audit_repository
        self.batch_run_repository = batch_run_repository

    def run_batch(
        self,
        payments: list[Payment],
    ) -> BatchResult:
        batch_run = self.batch_run_repository.create()
        run_id = batch_run.run_id

        total_at_risk = sum(
            payment.amount
            for payment in payments
        )

        total_recovered = 0.0

        rule_diagnoses = 0
        llm_diagnoses = 0

        successful_recoveries = 0
        failed_recoveries = 0
        pending_recoveries = 0

        manual_escalations = 0
        fraud_stops = 0
        low_confidence_escalations = 0
        retry_exhaustions = 0

        try:
            for payment in payments:
                self.payment_repository.save(
                    payment
                )

                diagnosis = (
                    self.diagnosis_service.diagnose(
                        payment
                    )
                )

                self.diagnosis_repository.save(
                    diagnosis
                )

                if diagnosis.source == DiagnosisSource.RULE:
                    rule_diagnoses += 1
                else:
                    llm_diagnoses += 1

                self.audit_repository.record(
                    payment_id=payment.payment_id,
                    run_id=run_id,
                    event_type=AuditEventType.DIAGNOSIS,
                    actor=enum_value(
                        diagnosis.source
                    ),
                    decision=enum_value(
                        diagnosis.root_cause
                    ),
                    metadata={
                        "confidence": (
                            diagnosis.confidence
                        ),
                        "recommended_action": (
                            enum_value(
                                diagnosis.recommended_action
                            )
                        ),
                        "reasoning": (
                            diagnosis.reasoning
                        ),
                        "model_name": (
                            diagnosis.model_name
                        ),
                        "prompt_version": (
                            diagnosis.prompt_version
                        ),
                    },
                )

                decision = decide_action(
                    payment,
                    diagnosis,
                )

                if diagnosis.root_cause == RootCause.FRAUD_FLAG:
                    fraud_stops += 1

                elif diagnosis.confidence < 0.50:
                    low_confidence_escalations += 1

                elif (
                    decision.max_attempts > 0
                    and payment.past_retry_count
                    >= decision.max_attempts
                ):
                    retry_exhaustions += 1

                if (
                    decision.action
                    == RecommendedAction.ESCALATE_MANUAL_REVIEW
                ):
                    manual_escalations += 1

                self.audit_repository.record(
                    payment_id=payment.payment_id,
                    run_id=run_id,
                    event_type=(
                        AuditEventType.POLICY_DECISION
                    ),
                    actor="policy_engine",
                    decision=enum_value(
                        decision.action
                    ),
                    policy_reason=decision.reason,
                    metadata={
                        "allowed": (
                            decision.allowed
                        ),
                        "attempt_number": (
                            decision.attempt_number
                        ),
                        "max_attempts": (
                            decision.max_attempts
                        ),
                    },
                )

                recovery_attempt = (
                    self.recovery_service.execute(
                        payment,
                        diagnosis,
                        decision,
                        run_id,
                    )
                )

                self.recovery_repository.save(
                    recovery_attempt
                )

                outcome = enum_value(
                    recovery_attempt.outcome
                )

                if (
                    outcome
                    == RecoveryOutcome.RECOVERED.value
                ):
                    successful_recoveries += 1
                    total_recovered += (
                        recovery_attempt.amount_recovered
                    )

                elif (
                    outcome
                    == RecoveryOutcome.FAILED.value
                ):
                    failed_recoveries += 1

                else:
                    pending_recoveries += 1

                self.audit_repository.record(
                    payment_id=payment.payment_id,
                    run_id=run_id,
                    event_type=(
                        AuditEventType.RECOVERY_ATTEMPT
                    ),
                    actor="recovery_simulator",
                    decision=outcome,
                    policy_reason=(
                        recovery_attempt.policy_reason
                    ),
                    metadata={
                        "action_type": (
                            enum_value(
                                recovery_attempt.action_type
                            )
                        ),
                        "attempt_number": (
                            recovery_attempt.attempt_number
                        ),
                        "amount_recovered": (
                            recovery_attempt.amount_recovered
                        ),
                    },
                )

            self.batch_run_repository.complete(
                run_id
            )

            self.payment_repository.session.commit()

        except Exception:
            self.batch_run_repository.fail(
                run_id
            )
            self.payment_repository.session.commit()
            raise

        recovery_rate = (
            total_recovered / total_at_risk
            if total_at_risk > 0
            else 0.0
        )

        return BatchResult(
            run_id=str(run_id),
            total_payments=len(payments),
            total_at_risk=total_at_risk,
            total_recovered=total_recovered,
            recovery_rate=recovery_rate,
            rule_diagnoses=rule_diagnoses,
            llm_diagnoses=llm_diagnoses,
            successful_recoveries=successful_recoveries,
            failed_recoveries=failed_recoveries,
            pending_recoveries=pending_recoveries,
            manual_escalations=manual_escalations,
            fraud_stops=fraud_stops,
            low_confidence_escalations=(
                low_confidence_escalations
            ),
            retry_exhaustions=retry_exhaustions,
        )