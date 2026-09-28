"""Append-only human claim decisions, with no backfilled approvals."""
from alembic import op
import sqlalchemy as sa
revision = '0021_run_claim_reviews'
down_revision = '0020_run_authority_evidence'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('run_claim_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_id', sa.String(80), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('revision', sa.String(64), nullable=False),
        sa.Column('reviewer_id', sa.String(128), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('payload_sha256', sa.String(64), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.UniqueConstraint('run_id', 'claim_id', 'sequence'))
    op.create_index('ix_run_claim_reviews_run_id', 'run_claim_reviews', ['run_id'])


def downgrade():
    op.drop_table('run_claim_reviews')
