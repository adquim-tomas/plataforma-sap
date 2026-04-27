"""upload_error: add error_code and sap_code

Revision ID: a1b2c3d4e5f6
Revises: 17082fb841a9
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "17082fb841a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "upload_error",
        sa.Column("error_code", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "upload_error",
        sa.Column("sap_code", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("upload_error", "sap_code")
    op.drop_column("upload_error", "error_code")
