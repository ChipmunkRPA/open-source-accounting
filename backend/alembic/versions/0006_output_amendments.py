"""Review history and monotonic term revisions; preserve every existing release counter."""
from alembic import op
import sqlalchemy as sa
revision = '0006_amendments'
down_revision = '0005_scopes'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('source_output_budgets', sa.Column('terms_revision', sa.Integer(), nullable=False, server_default='1'))
    op.create_table('source_output_amendments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('group_id', sa.String(120), sa.ForeignKey('source_output_budgets.group_id'), nullable=False),
        sa.Column('proposal', sa.JSON(), nullable=False),
        sa.Column('record_sha256', sa.String(64), nullable=False),
        sa.Column('submitted_by', sa.String(128), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('submitted_at', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('reviewed_by', sa.String(128), sa.ForeignKey('users.id')),
        sa.Column('reviewed_at', sa.Integer()),
        sa.Column('released_chars_at_apply', sa.BigInteger()),
        sa.Column('applied_terms_revision', sa.Integer()))
    op.create_index('ix_source_output_amendments_group_id', 'source_output_amendments', ['group_id'])


def downgrade():
    op.drop_table('source_output_amendments')
    op.drop_column('source_output_budgets', 'terms_revision')
