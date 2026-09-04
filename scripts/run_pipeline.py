from __future__ import annotations

import random
from datetime import datetime
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_db
from app.domain.models import Payment
from app.repositories.audit_repository import AuditRepository
from app.repositories.batch_run_repository import BatchRunRepository
from app.repositories.diagnosis_repository import DiagnosisRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.recovery_repository import RecoveryRepository
from app.services.diagnosis_service import DiagnosisService
from app.services.pipeline_service import PipelineService
from app.services.recovery_service import RecoverySimulator

CSV_PATH = "data/synthetic_payments.csv"
RANDOM_SEED = 42


def load_payments(
    path: str,
) -> list[Payment]:
    dataframe = pd.read_csv(path)

    payments: list[Payment] = []

    for row in dataframe.to_dict(
        orient="records"
    ):
        payments.append(
            Payment(
                payment_id=UUID(
                    str(row["payment_id"])
                ),
                customer_id=str(
                    row["customer_id"]
                ),
                amount=float(
                    row["amount"]
                ),
                currency=str(
                    row["currency"]
                ),
                decline_code=str(
                    row["decline_code"]
                ),
                customer_tenure_months=int(
                    row[
                        "customer_tenure_months"
                    ]
                ),
                past_retry_count=int(
                    row["past_retry_count"]
                ),
                failed_at=datetime.fromisoformat(
                    str(row["failed_at"])
                ),
                subscription_plan=str(
                    row["subscription_plan"]
                ),
            )
        )

    return payments


def build_pipeline(
    session: Session,
) -> PipelineService:
    return PipelineService(
        diagnosis_service=DiagnosisService(),
        recovery_service=RecoverySimulator(
            rng=random.Random(
                RANDOM_SEED
            )
        ),
        payment_repository=PaymentRepository(
            session
        ),
        diagnosis_repository=DiagnosisRepository(
            session
        ),
        recovery_repository=RecoveryRepository(
            session
        ),
        audit_repository=AuditRepository(
            session
        ),
        batch_run_repository=BatchRunRepository(
            session
        ),
    )


def main() -> None:
    init_db()

    payments = load_payments(
        CSV_PATH
    )

    with SessionLocal() as session:
        pipeline = build_pipeline(
            session
        )

        result = pipeline.run_batch(
            payments
        )

    print()
    print(
        "=============================================="
    )
    print(
        "           RECOVERX BATCH RESULTS"
    )
    print(
        "=============================================="
    )
    print(
        f"Run ID:                  {result.run_id}"
    )
    print(
        f"Payments processed:     {result.total_payments}"
    )
    print(
        f"At-risk revenue:        "
        f"INR {result.total_at_risk:,.2f}"
    )
    print(
        f"Recovered revenue:      "
        f"INR {result.total_recovered:,.2f}"
    )
    print(
        f"Recovery rate:          "
        f"{result.recovery_rate:.2%}"
    )
    print(
        "----------------------------------------------"
    )
    print(
        f"Rule diagnoses:         "
        f"{result.rule_diagnoses}"
    )
    print(
        f"Cohere diagnoses:       "
        f"{result.llm_diagnoses}"
    )
    print(
        "----------------------------------------------"
    )
    print(
        f"Successful recoveries:  "
        f"{result.successful_recoveries}"
    )
    print(
        f"Failed recoveries:      "
        f"{result.failed_recoveries}"
    )
    print(
        f"Pending recoveries:     "
        f"{result.pending_recoveries}"
    )
    print(
        "----------------------------------------------"
    )
    print(
        f"Manual escalations:     "
        f"{result.manual_escalations}"
    )
    print(
        f"Fraud hard stops:       "
        f"{result.fraud_stops}"
    )
    print(
        f"Low-confidence reviews: "
        f"{result.low_confidence_escalations}"
    )
    print(
        f"Retry exhaustion:       "
        f"{result.retry_exhaustions}"
    )
    print(
        "=============================================="
    )


if __name__ == "__main__":
    main()