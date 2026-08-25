"""add promocion_aplicada to ventas_detalles

Revision ID: 9f716576caba
Revises: df44819cd857
Create Date: 2026-08-19 20:48:12.821054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '9f716576caba'
down_revision: Union[str, None] = 'df44819cd857'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)  # 👈 inspect() acepta directamente la Connection sin lanzar error de tipo
    tables = inspector.get_table_names()

    if 'ventas_detalles' in tables:
        op.add_column('ventas_detalles', sa.Column('promocion_aplicada', sa.String(length=150), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if 'ventas_detalles' in tables:
        op.drop_column('ventas_detalles', 'promocion_aplicada')