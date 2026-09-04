from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.repositories.orm_models import (
    Base,
    BatchRunORM,
)


def test_get_all_run_metrics_returns_batch_runs() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False
        },
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run_id = uuid4()

        session.add(
            BatchRunORM(
                run_id=run_id,
                status="completed",
            )
        )

        session.commit()

        repository = AnalyticsRepository(
            session
        )

        results = (
            repository.get_all_run_metrics()
        )

        assert len(results) == 1

        metric = results[0]

        assert metric.run_id == run_id
        assert metric.status == "completed"
        assert metric.total_payments == 0
        assert metric.total_at_risk == 0.0
        assert metric.total_recovered == 0.0
        assert metric.recovery_rate == 0.0