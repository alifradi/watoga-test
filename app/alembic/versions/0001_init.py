"""TODO migration — enable PostGIS and create geography columns

Revision ID: 0001_init
Revises:
Create Date: 2025-09-04
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    
    # Create features table
    op.create_table(
        'features',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, default='queued'),
        sa.Column('attempts', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Add geography column to features
    op.execute("ALTER TABLE features ADD COLUMN geom geography(POINT, 4326) NOT NULL DEFAULT 'POINT EMPTY'::geography;")
    op.execute("ALTER TABLE features ALTER COLUMN geom DROP DEFAULT;")
    
    # Create GIST index on features geom column
    op.execute("CREATE INDEX idx_features_geom ON features USING GIST (geom);")
    
    # Create footprints table
    op.create_table(
        'footprints',
        sa.Column('feature_id', pg.UUID(as_uuid=True), sa.ForeignKey('features.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('buffer_m', sa.Integer, nullable=False),
        sa.Column('area_m2', sa.Float, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    
    # Add geography column to footprints
    op.execute("ALTER TABLE footprints ADD COLUMN geom geography(POLYGON, 4326) NOT NULL DEFAULT 'POLYGON EMPTY'::geography;")
    op.execute("ALTER TABLE footprints ALTER COLUMN geom DROP DEFAULT;")
    
    # Create GIST index on footprints geom column
    op.execute("CREATE INDEX idx_footprints_geom ON footprints USING GIST (geom);")

def downgrade():
    # Drop tables in reverse order
    op.drop_table('footprints')
    op.drop_table('features')
    # Note: We don't drop the PostGIS extension as it might be used by other applications
