from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import (
    DiagnosisSource,
    RecommendedAction,
    RootCause,
)
from app.domain.models import Diagnosis
from app.repositories.orm_models import DiagnosisORM


class DiagnosisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, diagnosis: Diagnosis) -> None:
        existing = self.session.get(
            DiagnosisORM,
            diagnosis.payment_id,
        )

        if existing is None:
            row = DiagnosisORM(
                payment_id=diagnosis.payment_id,
                root_cause=diagnosis.root_cause.value,
                confidence=diagnosis.confidence,
                source=diagnosis.source.value,
                recommended_action=diagnosis.recommended_action.value,
                reasoning=diagnosis.reasoning,
            )
            self.session.add(row)
            return

        existing.root_cause = diagnosis.root_cause.value
        existing.confidence = diagnosis.confidence
        existing.source = diagnosis.source.value
        existing.recommended_action = diagnosis.recommended_action.value
        existing.reasoning = diagnosis.reasoning

    def get_by_payment_id(self, payment_id):
        row = self.session.get(DiagnosisORM, payment_id)

        if row is None:
            return None

        return Diagnosis(
            payment_id=row.payment_id,
            root_cause=RootCause(row.root_cause),
            confidence=row.confidence,
            source=DiagnosisSource(row.source),
            recommended_action=RecommendedAction(row.recommended_action),
            reasoning=row.reasoning,
        )

    def list_all(self) -> list[Diagnosis]:
        statement = select(DiagnosisORM)
        rows = self.session.scalars(statement).all()

        return [
            Diagnosis(
                payment_id=row.payment_id,
                root_cause=RootCause(row.root_cause),
                confidence=row.confidence,
                source=DiagnosisSource(row.source),
                recommended_action=RecommendedAction(row.recommended_action),
                reasoning=row.reasoning,
            )
            for row in rows
        ]