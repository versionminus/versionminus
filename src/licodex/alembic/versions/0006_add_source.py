"""add source table and message.source column

Revision ID: 0006_add_source
Revises: 0005_drop_note_title
Create Date: 2025-10-08

Index policy note:
    We deliberately do NOT create an index on ``message.source`` here because
    current access patterns fetch messages by ``thread_id`` (already indexed)
    and then join/load related Source rows via their grouping id. An index on
    ``message.source`` only becomes valuable if you introduce frequent queries
    filtering directly on the retrieval group id (e.g. ``WHERE source = :uuid``)
    or analytics that scan by this column. If those patterns emerge, create a
    follow-up migration adding:

        op.create_index('ix_message_source', 'message', ['source'])

    Optionally as a partial index (PostgreSQL):

        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_message_source ON message(source) WHERE source IS NOT NULL")

    For now we keep writes cheaper by skipping it.
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '0006_add_source'
down_revision = '0005_drop_note_title'
branch_labels = None
depends_on = None


def upgrade() -> None:

    # 1. Add source column to message (nullable, no index)
    with op.batch_alter_table('message') as batch_op:
        batch_op.add_column(sa.Column('source', sa.Uuid(as_uuid=True), nullable=True))

    # 2. Create source table
    op.create_table(
        'source',
        sa.Column('pk', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False, index=True),  # retrieval grouping id
        sa.Column('note_id', sa.Uuid(as_uuid=True), sa.ForeignKey('note.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quote', sa.Text(), nullable=False, server_default=''),
    )


def downgrade() -> None:
    # Drop source table (indexes auto-dropped with table)
    op.drop_table('source')

    # Remove source column from message
    with op.batch_alter_table('message') as batch_op:
        batch_op.drop_column('source')
