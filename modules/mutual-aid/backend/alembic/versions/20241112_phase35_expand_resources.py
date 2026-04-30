"""phase35: expand resources with new categories and community features

Revision ID: phase35_resources
Revises: 20241112_add_resources_tables
Create Date: 2024-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase35_resources'
down_revision = '20241112_add_resources'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to resource_listings table
    op.add_column('resource_listings', sa.Column('subcategory', sa.String(length=100), nullable=True))
    op.add_column('resource_listings', sa.Column('is_community_contributed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('resource_listings', sa.Column('population_tags', postgresql.ARRAY(sa.String(length=50)), nullable=True))
    op.add_column('resource_listings', sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('resource_listings', sa.Column('verified_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('resource_listings', sa.Column('verification_count', sa.Integer(), nullable=True, server_default='0'))

    # Add foreign key for verified_by
    op.create_foreign_key(
        'fk_resource_listings_verified_by',
        'resource_listings',
        'users',
        ['verified_by'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for performance
    op.create_index('ix_resource_listings_subcategory', 'resource_listings', ['subcategory'], unique=False)
    op.create_index('ix_resource_listings_is_community_contributed', 'resource_listings', ['is_community_contributed'], unique=False)
    op.create_index('ix_resource_listings_population_tags', 'resource_listings', ['population_tags'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_resource_listings_population_tags', table_name='resource_listings', postgresql_using='gin')
    op.drop_index('ix_resource_listings_is_community_contributed', table_name='resource_listings')
    op.drop_index('ix_resource_listings_subcategory', table_name='resource_listings')

    # Drop foreign key
    op.drop_constraint('fk_resource_listings_verified_by', 'resource_listings', type_='foreignkey')

    # Drop columns
    op.drop_column('resource_listings', 'verification_count')
    op.drop_column('resource_listings', 'verified_at')
    op.drop_column('resource_listings', 'verified_by')
    op.drop_column('resource_listings', 'population_tags')
    op.drop_column('resource_listings', 'is_community_contributed')
    op.drop_column('resource_listings', 'subcategory')
