"""Shared source-output release ledger; contains no source or output body text."""
from alembic import op
import sqlalchemy as sa
revision = '0003_output'
down_revision = '0002_intake'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('source_output_budgets',
        sa.Column('group_id', sa.String(120), primary_key=True),
        sa.Column('limits_sha256', sa.String(64), nullable=False),
        sa.Column('released_chars', sa.BigInteger(), nullable=False))
    op.create_table('source_output_releases',
        sa.Column('group_id', sa.String(120), sa.ForeignKey('source_output_budgets.group_id'), primary_key=True),
        sa.Column('payload_sha256', sa.String(64), primary_key=True),
        sa.Column('character_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False))


def downgrade():
    op.drop_table('source_output_releases')
    op.drop_table('source_output_budgets')
