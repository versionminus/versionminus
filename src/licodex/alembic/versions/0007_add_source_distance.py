"""add distance column to source

Revision ID: 0007_add_source_distance
Revises: 0006_add_source
Create Date: 2025-10-08

Rationale:
    Store optional semantic retrieval distance (lower = closer). This enables
    UI ranking indicators and future analytics. Column is nullable to support
    legacy or heuristic fallback retrieval paths where no distance is computed.
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = '0007_add_source_distance'
down_revision = '0006_add_source'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('source') as batch_op:
        batch_op.add_column(sa.Column('distance', sa.Float(), nullable=True))
        # No index initially; access pattern fetches by retrieval group id.

def downgrade() -> None:
    with op.batch_alter_table('source') as batch_op:
        batch_op.drop_column('distance')