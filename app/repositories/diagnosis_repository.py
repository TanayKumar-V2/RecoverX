from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import (
    DiagnosisSource,
    RecommendedAction,
    RootCause,
)
from app.domain.models import Diagnosis
from app.repositories.orm_models import DiagnosisORM


def enum_value(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return str(value.value)

    return value


class DiagnosisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, diagnosis: Diagnosis) -> None:
        statement = select(DiagnosisORM).where(
            DiagnosisORM.payment_id == diagnosis.payment_id
        )

        existing = self.session.scalar(statement)

        if existing is None:
            row = DiagnosisORM(
                payment_id=diagnosis.payment_id,
                root_cause=enum_value(diagnosis.root_cause),
                confidence=diagnosis.confidence,
                source=enum_value(diagnosis.source),
                recommended_action=enum_value(
                    diagnosis.recommended_action
                ),
                reasoning=diagnosis.reasoning,
                model_name=diagnosis.model_name,
                prompt_version=diagnosis.prompt_version,
                latency_ms=diagnosis.latency_ms,
            )
            self.session.add(row)
            return

        existing.root_cause = enum_value(
            diagnosis.root_cause
        )
        existing.confidence = diagnosis.confidence
        existing.source = enum_value(
            diagnosis.source
        )
        existing.recommended_action = enum_value(
            diagnosis.recommended_action
        )
        existing.reasoning = diagnosis.reasoning
        existing.model_name = diagnosis.model_name
        existing.prompt_version = diagnosis.prompt_version
        existing.latency_ms = diagnosis.latency_ms

    def get_by_payment_id(
        self,
        payment_id: UUID,
    ) -> Diagnosis | None:
        statement = select(DiagnosisORM).where(
            DiagnosisORM.payment_id == payment_id
        )

        row = self.session.scalar(statement)

        if row is None:
            return None

        return Diagnosis(
            payment_id=row.payment_id,
            root_cause=RootCause(row.root_cause),
            confidence=row.confidence,
            source=DiagnosisSource(row.source),
            recommended_action=RecommendedAction(
                row.recommended_action
            ),
            reasoning=row.reasoning,
            model_name=row.model_name,
            prompt_version=row.prompt_version,
            latency_ms=row.latency_ms,
        )

    def list_all(self) -> list[Diagnosis]:
        statement = select(DiagnosisORM).order_by(
            DiagnosisORM.created_at
        )

        rows = self.session.scalars(statement).all()

        return [
            Diagnosis(
                payment_id=row.payment_id,
                root_cause=RootCause(row.root_cause),
                confidence=row.confidence,
                source=DiagnosisSource(row.source),
                recommended_action=RecommendedAction(
                    row.recommended_action
                ),
                reasoning=row.reasoning,
                model_name=row.model_name,
                prompt_version=row.prompt_version,
                latency_ms=row.latency_ms,
            )
            for row in rows
        ]