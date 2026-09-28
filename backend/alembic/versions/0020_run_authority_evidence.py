"""Preserve run relationship dependencies even when a linked record is removed."""
from alembic import op
import sqlalchemy as sa
revision = '0020_run_authority_evidence'
down_revision = '0019_authority_relationships'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('run_authority_evidence',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_id', sa.String(36), sa.ForeignKey('authority_relationships.id', ondelete='SET NULL')),
        sa.Column('source_evidence_id', sa.String(36), sa.ForeignKey('evidence.id', ondelete='SET NULL')),
        sa.Column('target_evidence_id', sa.String(36), sa.ForeignKey('evidence.id', ondelete='SET NULL')),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('payload_sha256', sa.String(64), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.UniqueConstraint('run_id', 'relationship_id'))
    op.create_index('ix_run_authority_evidence_run_id', 'run_authority_evidence', ['run_id'])


def downgrade():
    op.drop_table('run_authority_evidence')
