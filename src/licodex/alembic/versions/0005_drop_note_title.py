"""drop note.title column

Revision ID: 0005_drop_note_title
Revises: 0004_add_note_and_idea
Create Date: 2025-10-04
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_drop_note_title'
down_revision = '0004_add_note_and_idea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop index then column if exists (safe for re-run with IF EXISTS where supported)
    with op.batch_alter_table('note') as batch_op:
        try:
            batch_op.drop_index('ix_note_title')
        except Exception:  # pragma: no cover - defensive
            pass
        batch_op.drop_column('title')


def downgrade() -> None:
    # Recreate title column (empty string default) and index
    with op.batch_alter_table('note') as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=255), nullable=False, server_default=''))
        batch_op.create_index('ix_note_title', ['title'])
