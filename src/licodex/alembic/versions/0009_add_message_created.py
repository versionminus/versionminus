"""add created field to message

Revision ID: 0009_add_message_created
Revises: 0008_change_message_text
Create Date: 2025-01-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_add_message_created'
down_revision: Union[str, None] = '0008_change_message_text'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created column with default value for existing records
    op.add_column('message', sa.Column('created', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')))


def downgrade() -> None:
    # Remove created column
    op.drop_column('message', 'created')