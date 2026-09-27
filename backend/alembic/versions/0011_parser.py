"""Independent parser and citation review ledger; no approvals backfilled."""
from alembic import op
import sqlalchemy as sa
revision = '0011_parser'
down_revision = '0010_editorial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('parser_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('extraction_id', sa.String(36), sa.ForeignKey('source_extractions.id'), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.String(128), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('payload_sha256', sa.String(64), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.UniqueConstraint('extraction_id', 'sequence'))
    op.create_index('ix_parser_reviews_extraction_id', 'parser_reviews', ['extraction_id'])


def downgrade():
    op.drop_index('ix_parser_reviews_extraction_id', table_name='parser_reviews')
    op.drop_table('parser_reviews')
