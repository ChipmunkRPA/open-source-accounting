"""Preserve human technical-review decisions; never infer approval from legacy flags."""
from alembic import op
import sqlalchemy as sa
revision = '0010_editorial'
down_revision = '0009_discovery'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('editorial_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('reviewer_id', sa.String(128), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('decision', sa.String(30), nullable=False),
        sa.Column('review_revision', sa.String(64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('payload_sha256', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False))
    op.create_index('ix_editorial_reviews_source_id', 'editorial_reviews', ['source_id'])


def downgrade():
    op.drop_index('ix_editorial_reviews_source_id', table_name='editorial_reviews')
    op.drop_table('editorial_reviews')
