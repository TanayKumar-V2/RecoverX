"""add run tracking to diagnoses

Revision ID: c9d8f2a1e743
Revises: b7c4e21a9f31
Create Date: 2026-09-04 16:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "c9d8f2a1e743"
down_revision = "b7c4e21a9f31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table(
        "diagnoses"
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "run_id",
                sa.Uuid(),
                nullable=True,
            )
        )

        batch_op.create_index(
            "ix_diagnoses_run_id",
            ["run_id"],
        )

        batch_op.create_foreign_key(
            "fk_diagnoses_run_id",
            "batch_runs",
            ["run_id"],
            ["run_id"],
        )

        batch_op.create_unique_constraint(
            "uq_diagnoses_run_payment",
            ["run_id", "payment_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "diagnoses"
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_diagnoses_run_payment",
            type_="unique",
        )

        batch_op.drop_constraint(
            "fk_diagnoses_run_id",
            type_="foreignkey",
        )

        batch_op.drop_index(
            "ix_diagnoses_run_id"
        )

        batch_op.drop_column(
            "run_id"
        )