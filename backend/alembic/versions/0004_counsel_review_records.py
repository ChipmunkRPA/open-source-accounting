"""Persist scoped counsel decisions without importing private legal analysis."""
from alembic import op
import sqlalchemy as sa
revision = '0004_counsel'
down_revision = '0003_output'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('source_counsel_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('proposal', sa.JSON(), nullable=False),
        sa.Column('record_sha256', sa.String(64), nullable=False),
        sa.Column('submitted_by', sa.String(128), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('submitted_at', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('reviewed_by', sa.String(128), sa.ForeignKey('users.id')),
        sa.Column('reviewed_at', sa.Integer()),
        sa.Column('activated_policy_version', sa.Integer()),
        sa.Column('revoked_by', sa.String(128), sa.ForeignKey('users.id')),
        sa.Column('revoked_at', sa.Integer()),
        sa.Column('revocation_reason', sa.String(30)))
    op.create_index('ix_source_counsel_records_source_id', 'source_counsel_records', ['source_id'])


def downgrade():
    op.drop_table('source_counsel_records')
