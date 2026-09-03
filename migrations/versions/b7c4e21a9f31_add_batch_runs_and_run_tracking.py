"""add batch runs and run tracking

Revision ID: b7c4e21a9f31
Revises: a164327966a3
Create Date: 2026-09-03 14:10:00
"""

import sqlalchemy as sa
from alembic import op

revision = "b7c4e21a9f31"
down_revision = "a164327966a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_runs",
        sa.Column(
            "run_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("run_id"),
    )

    with op.batch_alter_table(
        "audit_events"
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "run_id",
                sa.Uuid(),
                nullable=True,
            )
        )
        batch_op.create_index(
            "ix_audit_events_run_id",
            ["run_id"],
        )
        batch_op.create_foreign_key(
            "fk_audit_events_run_id",
            "batch_runs",
            ["run_id"],
            ["run_id"],
        )

    with op.batch_alter_table(
        "recovery_attempts"
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "run_id",
                sa.Uuid(),
                nullable=True,
            )
        )
        batch_op.create_index(
            "ix_recovery_attempts_run_id",
            ["run_id"],
        )
        batch_op.create_foreign_key(
            "fk_recovery_attempts_run_id",
            "batch_runs",
            ["run_id"],
            ["run_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "recovery_attempts"
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_recovery_attempts_run_id",
            type_="foreignkey",
        )
        batch_op.drop_index(
            "ix_recovery_attempts_run_id"
        )
        batch_op.drop_column("run_id")

    with op.batch_alter_table(
        "audit_events"
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_audit_events_run_id",
            type_="foreignkey",
        )
        batch_op.drop_index(
            "ix_audit_events_run_id"
        )
        batch_op.drop_column("run_id")

    op.drop_table("batch_runs")