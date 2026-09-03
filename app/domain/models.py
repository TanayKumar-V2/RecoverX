from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    DiagnosisSource,
    PaymentStatus,
    RecommendedAction,
    RecoveryOutcome,
    RootCause,
)


class BatchRun(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    run_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    completed_at: datetime | None = None


class Payment(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: UUID = Field(default_factory=uuid4)
    customer_id: str
    amount: float = Field(gt=0)
    currency: str = "INR"

    decline_code: str

    customer_tenure_months: int = Field(ge=0)
    past_retry_count: int = Field(ge=0)

    failed_at: datetime
    subscription_plan: str

    status: PaymentStatus = PaymentStatus.FAILED


class Diagnosis(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: UUID

    root_cause: RootCause
    confidence: float = Field(ge=0, le=1)

    source: DiagnosisSource

    recommended_action: RecommendedAction

    reasoning: str = Field(min_length=1)

    model_name: str | None = None
    prompt_version: str | None = None
    latency_ms: float | None = Field(default=None, ge=0)


class PolicyDecision(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: UUID

    action: RecommendedAction

    allowed: bool

    reason: str = Field(min_length=1)

    attempt_number: int = Field(ge=0)

    max_attempts: int = Field(ge=0)


class RecoveryAttempt(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    action_id: UUID = Field(default_factory=uuid4)
    run_id: UUID = Field(default_factory=uuid4)
    payment_id: UUID

    action_type: RecommendedAction

    attempt_number: int = Field(ge=1)

    outcome: RecoveryOutcome

    amount_recovered: float = Field(ge=0)

    timestamp: datetime

    policy_reason: str = Field(min_length=1)