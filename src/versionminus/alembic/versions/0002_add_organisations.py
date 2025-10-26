"""add organisations and user fk

Revision ID: 0002_add_organisations
Revises: 0001_initial
Create Date: 2025-09-29
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '0002_add_organisations'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'organisations',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_organisations_name', 'organisations', ['name'])

    # add fk column to users
    op.add_column('users', sa.Column('organisation_id', sa.Uuid(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_users_organisation_id_organisations',
        'users', 'organisations', ['organisation_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_users_organisation_id', 'users', ['organisation_id'])


def downgrade() -> None:
    op.drop_index('ix_users_organisation_id', table_name='users')
    op.drop_constraint('fk_users_organisation_id_organisations', 'users', type_='foreignkey')
    op.drop_column('users', 'organisation_id')
    op.drop_index('ix_organisations_name', table_name='organisations')
    op.drop_table('organisations')
