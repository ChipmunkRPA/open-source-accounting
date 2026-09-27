"""Immutable unreviewed candidates derived from an authorized stored index."""
from alembic import op
import sqlalchemy as sa
revision = '0009_discovery'
down_revision = '0008_budgets'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('source_discoveries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('artifact_id', sa.String(36), sa.ForeignKey('source_artifacts.id'), nullable=False),
        sa.Column('adapter_version', sa.String(100), nullable=False),
        sa.Column('recipe_sha256', sa.String(64), nullable=False),
        sa.Column('normalized_sha256', sa.String(64), nullable=False),
        sa.Column('object_key', sa.String(250), nullable=False),
        sa.Column('candidate_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.UniqueConstraint('artifact_id', 'adapter_version', 'recipe_sha256'))
    op.create_index('ix_source_discoveries_artifact_id', 'source_discoveries', ['artifact_id'])


def downgrade():
    op.drop_index('ix_source_discoveries_artifact_id', table_name='source_discoveries')
    op.drop_table('source_discoveries')
