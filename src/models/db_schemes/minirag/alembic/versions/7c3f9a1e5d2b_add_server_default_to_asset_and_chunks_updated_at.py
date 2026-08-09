"""add server_default to asset.updated_at and chunks.updated_at

Revision ID: 7c3f9a1e5d2b
Revises: 0ed3d2214640
Create Date: 2026-07-29 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c3f9a1e5d2b'
down_revision: Union[str, Sequence[str], None] = '0ed3d2214640'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('asset', 'updated_at',
        server_default=sa.text('now()'))
    op.alter_column('chunks', 'updated_at',
        server_default=sa.text('now()'))


def downgrade() -> None:
    op.alter_column('asset', 'updated_at',
        server_default=None)
    op.alter_column('chunks', 'updated_at',
        server_default=None)
