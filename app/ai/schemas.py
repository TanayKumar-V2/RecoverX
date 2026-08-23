from pydantic import BaseModel, Field

from app.domain.enums import RecommendedAction, RootCause


class CohereDiagnosisResponse(BaseModel):
    root_cause: RootCause

    confidence: float = Field(
        ge=0,
        le=1,
    )

    recommended_action: RecommendedAction

    reasoning: str = Field(
        min_length=1,
    )
