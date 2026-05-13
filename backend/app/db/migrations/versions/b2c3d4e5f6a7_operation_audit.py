"""operation_audit: per-row snapshot before/after

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operation_audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("sap_module", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column("fields_before", postgresql.JSONB(), nullable=True),
        sa.Column("fields_after", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OK", "FAIL", name="operationstatus"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["batch_id"], ["upload_batch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_operation_audit_batch_id"),
        "operation_audit",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_operation_audit_username"),
        "operation_audit",
        ["username"],
        unique=False,
    )
    op.create_index(
        op.f("ix_operation_audit_sap_module"),
        "operation_audit",
        ["sap_module"],
        unique=False,
    )
    op.create_index(
        op.f("ix_operation_audit_resource_id"),
        "operation_audit",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_operation_audit_created_at"),
        "operation_audit",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_operation_audit_created_at"), table_name="operation_audit"
    )
    op.drop_index(
        op.f("ix_operation_audit_resource_id"), table_name="operation_audit"
    )
    op.drop_index(
        op.f("ix_operation_audit_sap_module"), table_name="operation_audit"
    )
    op.drop_index(
        op.f("ix_operation_audit_username"), table_name="operation_audit"
    )
    op.drop_index(
        op.f("ix_operation_audit_batch_id"), table_name="operation_audit"
    )
    op.drop_table("operation_audit")
    sa.Enum(name="operationstatus").drop(op.get_bind(), checkfirst=False)
