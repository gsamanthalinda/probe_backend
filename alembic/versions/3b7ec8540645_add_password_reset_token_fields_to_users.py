"""Add password reset token fields to users

Revision ID: 3b7ec8540645
Revises: 7f177b2fe7bf
Create Date: 2026-08-15 14:40:39.501623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b7ec8540645'
down_revision: Union[str, Sequence[str], None] = '7f177b2fe7bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_users_reset_token', 'users', ['reset_token'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_users_reset_token', table_name='users')
    op.drop_column('users', 'reset_token_expires_at')
    op.drop_column('users', 'reset_token')
