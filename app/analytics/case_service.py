from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.models import Diagnosis, Payment, RecoveryAttempt
from app.repositories.audit_repository import AuditRepository
from app.repositories.diagnosis_repository import DiagnosisRepository
from app.repositories.orm_models import AuditEventORM
from app.repositories.payment_repository import PaymentRepository
from app.repositories.recovery_repository import RecoveryRepository


@dataclass(frozen=True, slots=True)
class CaseDetails:
    run_id: UUID
    payment: Payment
    diagnosis: Diagnosis | None
    recovery_attempts: list[RecoveryAttempt]
    audit_events: list[AuditEventORM]


class CaseAnalyticsService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        diagnosis_repository: DiagnosisRepository,
        recovery_repository: RecoveryRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self.payment_repository = payment_repository
        self.diagnosis_repository = diagnosis_repository
        self.recovery_repository = recovery_repository
        self.audit_repository = audit_repository

    def get_case(
        self,
        run_id: UUID,
        payment_id: UUID,
    ) -> CaseDetails | None:
        payment = self.payment_repository.get_by_id(
            payment_id
        )

        if payment is None:
            return None

        diagnosis = (
            self.diagnosis_repository.get_by_payment_id(
                payment_id
            )
        )

        recovery_attempts = (
            self.recovery_repository.get_by_run_and_payment(
                run_id,
                payment_id,
            )
        )

        audit_events = (
            self.audit_repository.get_for_run_and_payment(
                run_id,
                payment_id,
            )
        )

        return CaseDetails(
            run_id=run_id,
            payment=payment,
            diagnosis=diagnosis,
            recovery_attempts=recovery_attempts,
            audit_events=audit_events,
        )