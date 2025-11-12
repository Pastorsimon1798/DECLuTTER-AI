"""add resources tables for pantry locator

Revision ID: 20241112_add_resources
Revises: 20241112_add_shifts
Create Date: 2024-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '20241112_add_resources'
down_revision = '20241112_add_shifts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create resource_listings table
    op.create_table(
        'resource_listings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('external_id', sa.String(200), unique=True),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('location_address', sa.Text),
        sa.Column('location_point', geoalchemy2.Geography('POINT', srid=4326)),
        sa.Column('location_geohash', sa.String(12)),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(255)),
        sa.Column('website', sa.String(500)),
        sa.Column('hours', postgresql.JSONB),
        sa.Column('services', postgresql.ARRAY(sa.Text)),
        sa.Column('languages', postgresql.ARRAY(sa.String(5))),
        sa.Column('accessibility_features', postgresql.ARRAY(sa.Text)),
        sa.Column('eligibility_requirements', sa.Text),
        sa.Column('documents_required', postgresql.ARRAY(sa.Text)),
        sa.Column('last_verified_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('cached_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('cache_expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create resource_bookmarks table
    op.create_table(
        'resource_bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resource_listings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'resource_id', name='resource_bookmark_unique'),
    )

    # Create indexes
    op.create_index('idx_resources_category', 'resource_listings', ['category'])
    op.create_index('idx_resources_geohash', 'resource_listings', ['location_geohash'])
    op.create_index('idx_resources_external_id', 'resource_listings', ['external_id'])
    op.create_index('idx_resources_cache_expires', 'resource_listings', ['cache_expires_at'])

    op.create_index('idx_bookmarks_user', 'resource_bookmarks', ['user_id'])
    op.create_index('idx_bookmarks_resource', 'resource_bookmarks', ['resource_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('resource_bookmarks')
    op.drop_table('resource_listings')
