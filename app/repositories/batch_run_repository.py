from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import BatchRun
from app.repositories.orm_models import BatchRunORM


class BatchRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self) -> BatchRun:
        batch_run = BatchRun()

        row = BatchRunORM(
            run_id=batch_run.run_id,
            started_at=batch_run.started_at,
            status="running",
        )

        self.session.add(row)
        self.session.flush()

        return batch_run

    def complete(
        self,
        run_id: UUID,
    ) -> None:
        row = self.session.get(
            BatchRunORM,
            run_id,
        )

        if row is None:
            raise ValueError(
                f"Batch run {run_id} does not exist"
            )

        row.completed_at = datetime.now(UTC)
        row.status = "completed"

    def fail(
        self,
        run_id: UUID,
    ) -> None:
        row = self.session.get(
            BatchRunORM,
            run_id,
        )

        if row is None:
            raise ValueError(
                f"Batch run {run_id} does not exist"
            )

        row.completed_at = datetime.now(UTC)
        row.status = "failed"

    def get_by_id(
        self,
        run_id: UUID,
    ) -> BatchRunORM | None:
        return self.session.get(
            BatchRunORM,
            run_id,
        )

    def list_all(self) -> list[BatchRunORM]:
        statement = select(BatchRunORM).order_by(
            BatchRunORM.started_at.desc()
        )

        return list(
            self.session.scalars(statement).all()
        )