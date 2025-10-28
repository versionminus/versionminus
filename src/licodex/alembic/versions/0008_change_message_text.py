"""change message.content/response to TEXT

Revision ID: 0008_change_message_text
Revises: 0007_add_source_distance
Create Date: 2025-10-09

Rationale:
    Original schema used ``VARCHAR(255)`` for both user ``content`` and
    assistant ``response``. LLM + RAG interactions frequently exceed this,
    leading to ``StringDataRightTruncationError``. We now use ``TEXT`` which
    comfortably stores multi‑KB replies. No downcast risk on PostgreSQL.
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = '0008_change_message_text'
down_revision = '0007_add_source_distance'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('message') as batch_op:
        batch_op.alter_column('content', type_=sa.Text())
        batch_op.alter_column('response', type_=sa.Text())


def downgrade() -> None:
    # Revert to previous bounded length (may truncate existing long rows if executed!)
    with op.batch_alter_table('message') as batch_op:
        batch_op.alter_column('content', type_=sa.String(length=255))
        batch_op.alter_column('response', type_=sa.String(length=255))
