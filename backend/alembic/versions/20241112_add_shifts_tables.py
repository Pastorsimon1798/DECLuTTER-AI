"""add shifts tables for volunteer scheduling

Revision ID: 20241112_add_shifts
Revises: 20241112_initial_schema
Create Date: 2024-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '20241112_add_shifts'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('location_geohash', sa.String(12)),
        sa.Column('location_point', geoalchemy2.Geography('POINT', srid=4326)),
        sa.Column('address', sa.Text),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(255)),
        sa.Column('website', sa.String(500)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create shifts table
    op.create_table(
        'shifts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('location', sa.String(500)),
        sa.Column('location_point', geoalchemy2.Geography('POINT', srid=4326)),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('capacity', sa.Integer, nullable=False, server_default='1'),
        sa.Column('filled_count', sa.Integer, server_default='0'),
        sa.Column('recurrence_rule', sa.Text),
        sa.Column('reminder_24h', sa.Boolean, server_default='true'),
        sa.Column('reminder_2h', sa.Boolean, server_default='true'),
        sa.Column('coordinator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('status', sa.String(20), server_default='open', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'open', 'full', 'completed', 'cancelled')", name='shifts_status_check'),
    )

    # Create shift_signups table
    op.create_table(
        'shift_signups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shifts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('volunteer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), server_default='confirmed', nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('reminder_24h_sent', sa.Boolean, server_default='false'),
        sa.Column('reminder_2h_sent', sa.Boolean, server_default='false'),
        sa.Column('signed_up_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('cancelled_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint("status IN ('confirmed', 'cancelled', 'no_show', 'completed')", name='shift_signups_status_check'),
        sa.UniqueConstraint('shift_id', 'volunteer_id', name='shift_signup_unique'),
    )

    # Create indexes
    op.create_index('idx_shifts_start', 'shifts', ['start_time'])
    op.create_index('idx_shifts_org', 'shifts', ['organization_id'])
    op.create_index('idx_shifts_status', 'shifts', ['status'])

    op.create_index('idx_signups_shift', 'shift_signups', ['shift_id'])
    op.create_index('idx_signups_volunteer', 'shift_signups', ['volunteer_id'])
    op.create_index('idx_signups_status', 'shift_signups', ['status'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('shift_signups')
    op.drop_table('shifts')
    op.drop_table('organizations')
