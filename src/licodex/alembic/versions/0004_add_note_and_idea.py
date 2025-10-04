"""add note and idea models

Revision ID: 0004_add_note_and_idea
Revises: 0003_add_chat_models_rm_org
Create Date: 2025-10-04
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '0004_add_note_and_idea'
down_revision = '0003_add_chat_models_rm_org'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # note table
    op.create_table(
        'note',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'DELETED', name='notestatus'), nullable=False, server_default='AVAILABLE'),
        sa.Column('embedded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index('ix_note_title', 'note', ['title'])
    op.create_index('ix_note_user_id', 'note', ['user_id'])

    # idea table
    op.create_table(
        'idea',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('relationship_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('note_id', sa.Uuid(as_uuid=True), sa.ForeignKey('note.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.Enum('AVAILABLE', 'DELETED', name='ideastatus'), nullable=False, server_default='AVAILABLE'),
        sa.Column('embedded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index('ix_idea_title', 'idea', ['title'])
    op.create_index('ix_idea_note_id', 'idea', ['note_id'])


def downgrade() -> None:
    op.drop_index('ix_idea_note_id', table_name='idea')
    op.drop_index('ix_idea_title', table_name='idea')
    op.drop_table('idea')
    op.drop_index('ix_note_user_id', table_name='note')
    op.drop_index('ix_note_title', table_name='note')
    op.drop_table('note')
    # drop enums
    op.execute("DROP TYPE IF EXISTS ideastatus")
    op.execute("DROP TYPE IF EXISTS notestatus")
