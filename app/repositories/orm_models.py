from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BatchRunORM(Base):
    __tablename__ = "batch_runs"

    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="running",
    )

    recovery_attempts: Mapped[list[RecoveryAttemptORM]] = relationship(
        back_populates="batch_run",
    )

    audit_events: Mapped[list[AuditEventORM]] = relationship(
        back_populates="batch_run",
    )


class PaymentORM(Base):
    __tablename__ = "payments"

    payment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    customer_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    decline_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    customer_tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    past_retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    subscription_plan: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="failed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    diagnoses: Mapped[list[DiagnosisORM]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    recovery_attempts: Mapped[list[RecoveryAttemptORM]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    audit_events: Mapped[list[AuditEventORM]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )


class DiagnosisORM(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    payment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("payments.payment_id"),
        nullable=False,
        index=True,
    )

    root_cause: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    recommended_action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    reasoning: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    prompt_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    payment: Mapped[PaymentORM] = relationship(
        back_populates="diagnoses",
    )


class RecoveryAttemptORM(Base):
    __tablename__ = "recovery_attempts"

    action_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batch_runs.run_id"),
        nullable=True,
        index=True,
    )

    payment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("payments.payment_id"),
        nullable=False,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    outcome: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    amount_recovered: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    policy_reason: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    payment: Mapped[PaymentORM] = relationship(
        back_populates="recovery_attempts",
    )

    batch_run: Mapped[BatchRunORM | None] = relationship(
        back_populates="recovery_attempts",
    )


class AuditEventORM(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batch_runs.run_id"),
        nullable=True,
        index=True,
    )

    payment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("payments.payment_id"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    actor: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    decision: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    policy_reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    payment: Mapped[PaymentORM] = relationship(
        back_populates="audit_events",
    )

    batch_run: Mapped[BatchRunORM | None] = relationship(
        back_populates="audit_events",
    )