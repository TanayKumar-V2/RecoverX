from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import PaymentStatus
from app.domain.models import Payment
from app.repositories.orm_models import PaymentORM


def enum_value(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return str(value.value)

    return value


class PaymentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, payment: Payment) -> None:
        existing = self.session.get(
            PaymentORM,
            payment.payment_id,
        )

        if existing is None:
            row = PaymentORM(
                payment_id=payment.payment_id,
                customer_id=payment.customer_id,
                amount=payment.amount,
                currency=payment.currency,
                decline_code=payment.decline_code,
                customer_tenure_months=payment.customer_tenure_months,
                past_retry_count=payment.past_retry_count,
                failed_at=payment.failed_at,
                subscription_plan=payment.subscription_plan,
                status=enum_value(payment.status),
            )
            self.session.add(row)
            return

        existing.customer_id = payment.customer_id
        existing.amount = payment.amount
        existing.currency = payment.currency
        existing.decline_code = payment.decline_code
        existing.customer_tenure_months = payment.customer_tenure_months
        existing.past_retry_count = payment.past_retry_count
        existing.failed_at = payment.failed_at
        existing.subscription_plan = payment.subscription_plan
        existing.status = enum_value(payment.status)

    def get_by_id(
        self,
        payment_id: UUID,
    ) -> Payment | None:
        row = self.session.get(
            PaymentORM,
            payment_id,
        )

        if row is None:
            return None

        return Payment(
            payment_id=row.payment_id,
            customer_id=row.customer_id,
            amount=row.amount,
            currency=row.currency,
            decline_code=row.decline_code,
            customer_tenure_months=row.customer_tenure_months,
            past_retry_count=row.past_retry_count,
            failed_at=row.failed_at,
            subscription_plan=row.subscription_plan,
            status=PaymentStatus(row.status),
        )

    def list_all(self) -> list[Payment]:
        statement = select(PaymentORM)
        rows = self.session.scalars(statement).all()

        return [
            Payment(
                payment_id=row.payment_id,
                customer_id=row.customer_id,
                amount=row.amount,
                currency=row.currency,
                decline_code=row.decline_code,
                customer_tenure_months=row.customer_tenure_months,
                past_retry_count=row.past_retry_count,
                failed_at=row.failed_at,
                subscription_plan=row.subscription_plan,
                status=PaymentStatus(row.status),
            )
            for row in rows
        ]