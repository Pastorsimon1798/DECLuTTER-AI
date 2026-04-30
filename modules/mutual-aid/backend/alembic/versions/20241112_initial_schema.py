"""Initial database schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('pseudonym', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(255), unique=True, nullable=True),
        sa.Column('phone_hash', sa.String(64), unique=True, nullable=True),
        sa.Column('phone_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('locale', sa.String(5), default='en', nullable=False),
        sa.Column('timezone', sa.String(50), default='America/New_York', nullable=False),
        sa.Column('notification_prefs', postgresql.JSONB, nullable=False, server_default='{"sms": true, "email": true, "push": false}'),
        sa.Column('location_geohash', sa.String(12), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=True),
    )

    op.create_index('idx_users_pseudonym', 'users', ['pseudonym'])
    op.create_index('idx_users_geohash', 'users', ['location_geohash'])
    op.create_index('idx_users_phone_hash', 'users', ['phone_hash'])

    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('skills', postgresql.ARRAY(sa.Text), default=[], nullable=False, server_default='{}'),
        sa.Column('languages', postgresql.ARRAY(sa.String(5)), default=[], nullable=False, server_default='{}'),
        sa.Column('accessibility_needs', postgresql.ARRAY(sa.Text), default=[], nullable=False, server_default='{}'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('pronouns', sa.String(20), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create posts table
    op.create_table(
        'posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('type', sa.String(10), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('location_geohash', sa.String(12), nullable=False),
        sa.Column('location_point', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('radius_meters', sa.Integer, default=1000, nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('visibility', sa.String(20), default='public', nullable=False),
        sa.Column('status', sa.String(20), default='open', nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint("type IN ('NEED', 'OFFER')", name='check_post_type'),
        sa.CheckConstraint("visibility IN ('public', 'circles', 'private')", name='check_post_visibility'),
        sa.CheckConstraint("status IN ('open', 'matched', 'in_progress', 'completed', 'cancelled')", name='check_post_status'),
    )

    op.create_index('idx_posts_geohash', 'posts', ['location_geohash'])
    op.create_index('idx_posts_type', 'posts', ['type'])
    op.create_index('idx_posts_status', 'posts', ['status'])
    op.create_index('idx_posts_category', 'posts', ['category'])
    op.create_index('idx_posts_author', 'posts', ['author_id'])

    # Create matches table
    op.create_table(
        'matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id'), nullable=False),
        sa.Column('responder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('method', sa.String(20), default='in_app', nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("method IN ('in_app', 'sms', 'phone')", name='check_match_method'),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'declined', 'completed', 'cancelled')", name='check_match_status'),
    )

    op.create_index('idx_matches_post', 'matches', ['post_id'])
    op.create_index('idx_matches_responder', 'matches', ['responder_id'])
    op.create_index('idx_matches_requester', 'matches', ['requester_id'])

    # Create contact_tokens table
    op.create_table(
        'contact_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('encrypted_value', sa.Text, nullable=False),
        sa.Column('shared_with_user', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('shared_via_post', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id'), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("kind IN ('phone', 'email', 'signal', 'whatsapp')", name='check_contact_kind'),
    )

    op.create_index('idx_contact_tokens_user', 'contact_tokens', ['user_id'])
    op.create_index('idx_contact_tokens_shared_with', 'contact_tokens', ['shared_with_user'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('channels', postgresql.ARRAY(sa.String(20)), default=['in_app'], nullable=False, server_default='{"in_app"}'),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('read_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'sent', 'failed', 'read')", name='check_notification_status'),
    )

    op.create_index('idx_notifications_user', 'notifications', ['user_id'])
    op.create_index('idx_notifications_status', 'notifications', ['status'])
    op.create_index('idx_notifications_created', 'notifications', ['created_at'])

    # Create activity_log table
    op.create_table(
        'activity_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('idx_activity_log_type', 'activity_log', ['event_type'])
    op.create_index('idx_activity_log_created', 'activity_log', ['created_at'])

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reported_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reported_post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id'), nullable=True),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("reason IN ('spam', 'harassment', 'inappropriate', 'other')", name='check_report_reason'),
        sa.CheckConstraint("status IN ('pending', 'investigating', 'resolved', 'dismissed')", name='check_report_status'),
    )

    op.create_index('idx_reports_status', 'reports', ['status'])
    op.create_index('idx_reports_reporter', 'reports', ['reporter_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('reports')
    op.drop_table('activity_log')
    op.drop_table('notifications')
    op.drop_table('contact_tokens')
    op.drop_table('matches')
    op.drop_table('posts')
    op.drop_table('user_profiles')
    op.drop_table('users')

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "postgis"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
