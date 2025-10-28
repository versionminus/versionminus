"""add chat thread & message models, remove organisations

Revision ID: 0003_add_chat_models_rm_org
Revises: 0002_add_organisations
Create Date: 2025-09-30
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '0003_add_chat_models_rm_org'
down_revision = '0002_add_organisations'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Drop FK, index, and column from users referencing organisations
    # Use batch_alter_table for SQLite compatibility.
    with op.batch_alter_table('users') as batch_op:
        # Constraint name must match the one created in 0002
        batch_op.drop_constraint('fk_users_organisation_id_organisations', type_='foreignkey')
        batch_op.drop_index('ix_users_organisation_id')
        batch_op.drop_column('organisation_id')

    # 2. Drop organisations table & its index
    op.drop_index('ix_organisations_name', table_name='organisations')
    op.drop_table('organisations')

    # 3. Create thread table
    op.create_table(
        'thread',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(length=255), nullable=False, unique=True),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    )
    # unique already implies an index; explicit index kept for clarity/lookup speed if desired
    op.create_index('ix_thread_title', 'thread', ['title'])
    op.create_index('ix_thread_user_id', 'thread', ['user_id'])

    # 4. Create message table
    op.create_table(
        'message',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('content', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('response', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('thread_id', sa.Uuid(as_uuid=True), sa.ForeignKey('thread.id', ondelete='CASCADE'), nullable=False),
    )
    op.create_index('ix_message_thread_id', 'message', ['thread_id'])

def downgrade() -> None:
    # Reverse creation of message & thread tables
    op.drop_index('ix_message_thread_id', table_name='message')
    op.drop_table('message')
    op.drop_index('ix_thread_user_id', table_name='thread')
    op.drop_index('ix_thread_title', table_name='thread')
    op.drop_table('thread')

    # Recreate organisations table
    op.create_table(
        'organisations',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_organisations_name', 'organisations', ['name'])

    # Re-add organisation_id column and constraint to users
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('organisation_id', sa.Uuid(as_uuid=True), nullable=True))
        batch_op.create_index('ix_users_organisation_id', ['organisation_id'])
        batch_op.create_foreign_key(
            'fk_users_organisation_id_organisations', 'organisations', ['organisation_id'], ['id'], ondelete='SET NULL'
        )
