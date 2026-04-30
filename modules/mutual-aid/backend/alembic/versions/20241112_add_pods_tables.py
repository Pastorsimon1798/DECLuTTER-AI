"""add pods tables

Revision ID: phase4_pods
Revises: phase35_resources
Create Date: 2024-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase4_pods'
down_revision = 'phase35_resources'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pods table
    op.create_table(
        'pods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_members', sa.Integer(), nullable=True, server_default='20'),
        sa.Column('check_in_frequency_days', sa.Integer(), nullable=True, server_default='7'),
        sa.Column('enable_wellness_alerts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('missed_checkins_threshold', sa.Integer(), nullable=True, server_default='2'),
        sa.Column('enable_sos_broadcasts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_pods_created_by', 'pods', ['created_by'])
    op.create_index('ix_pods_created_at', 'pods', ['created_at'])

    # Create pod_members table
    op.create_table(
        'pod_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pod_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('last_check_in_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('consecutive_missed_checkins', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('joined_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pod_id'], ['pods.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('pod_id IS NOT NULL AND user_id IS NOT NULL', name='pod_member_check'),
    )
    op.create_index('ix_pod_members_pod_id', 'pod_members', ['pod_id'])
    op.create_index('ix_pod_members_user_id', 'pod_members', ['user_id'])
    op.create_index('ix_pod_members_pod_user', 'pod_members', ['pod_id', 'user_id'])
    op.create_index('ix_pod_members_status', 'pod_members', ['status'])

    # Create check_ins table
    op.create_table(
        'check_ins',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pod_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('member_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['pod_id'], ['pods.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['pod_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_check_ins_pod_id', 'check_ins', ['pod_id'])
    op.create_index('ix_check_ins_user_id', 'check_ins', ['user_id'])
    op.create_index('ix_check_ins_created_at', 'check_ins', ['created_at'])
    op.create_index('ix_check_ins_status', 'check_ins', ['status'])

    # Create sos_broadcasts table
    op.create_table(
        'sos_broadcasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pod_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('urgency', sa.String(length=20), nullable=True, server_default='high'),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['pod_id'], ['pods.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_sos_broadcasts_pod_id', 'sos_broadcasts', ['pod_id'])
    op.create_index('ix_sos_broadcasts_user_id', 'sos_broadcasts', ['user_id'])
    op.create_index('ix_sos_broadcasts_created_at', 'sos_broadcasts', ['created_at'])
    op.create_index('ix_sos_broadcasts_is_resolved', 'sos_broadcasts', ['is_resolved'])

    # Create pod_posts table
    op.create_table(
        'pod_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pod_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('post_type', sa.String(length=20), nullable=True, server_default='general'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pinned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pod_id'], ['pods.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pinned_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_pod_posts_pod_id', 'pod_posts', ['pod_id'])
    op.create_index('ix_pod_posts_user_id', 'pod_posts', ['user_id'])
    op.create_index('ix_pod_posts_created_at', 'pod_posts', ['created_at'])
    op.create_index('ix_pod_posts_is_pinned', 'pod_posts', ['is_pinned'])


def downgrade() -> None:
    op.drop_table('pod_posts')
    op.drop_table('sos_broadcasts')
    op.drop_table('check_ins')
    op.drop_table('pod_members')
    op.drop_table('pods')
