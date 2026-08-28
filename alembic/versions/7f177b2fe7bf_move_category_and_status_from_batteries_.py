"""Move category and status from batteries to sensor_readings

Revision ID: 7f177b2fe7bf
Revises: 
Create Date: 2026-08-15 11:16:07.614302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7f177b2fe7bf'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type
    readingstatus = postgresql.ENUM('REUSABLE', 'RECOVERABLE', 'DISPOSABLE', name='readingstatus')
    readingstatus.create(op.get_bind())

    # Add columns as nullable first so existing rows don't fail
    op.add_column('sensor_readings', sa.Column('category', sa.String(), nullable=True))
    op.add_column('sensor_readings', sa.Column('status', readingstatus, nullable=True))

    # Backfill existing sensor_readings with safe defaults
    op.execute("UPDATE sensor_readings SET category = 'C', status = 'DISPOSABLE' WHERE category IS NULL")

    # Now make them NOT NULL
    op.alter_column('sensor_readings', 'category', nullable=False)
    op.alter_column('sensor_readings', 'status', nullable=False)

    # Drop category and status from batteries
    op.drop_column('batteries', 'category')
    op.drop_column('batteries', 'status')


def downgrade() -> None:
    # Add category and status back to batteries
    op.add_column('batteries', sa.Column('category', sa.VARCHAR(), nullable=False))
    op.add_column('batteries', sa.Column('status', postgresql.ENUM('AVAILABLE', 'PROCESSING', name='batterystatus'), nullable=False))

    # Drop category and status from sensor_readings
    op.drop_column('sensor_readings', 'status')
    op.drop_column('sensor_readings', 'category')

    # Drop enum
    readingstatus = postgresql.ENUM('REUSABLE', 'RECOVERABLE', 'DISPOSABLE', name='readingstatus')
    readingstatus.drop(op.get_bind())
