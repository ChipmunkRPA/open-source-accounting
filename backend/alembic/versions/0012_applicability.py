"""Independent general applicability decisions; no date/approval backfill."""
from alembic import op
import sqlalchemy as sa
revision='0012_applicability'
down_revision='0011_parser'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('applicability_reviews',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id'),nullable=False),
        sa.Column('reviewer_id',sa.String(128),sa.ForeignKey('users.id',ondelete='SET NULL')),
        sa.Column('payload',sa.JSON(),nullable=False),
        sa.Column('payload_sha256',sa.String(64),nullable=False),
        sa.Column('created_at',sa.Integer(),nullable=False))
    op.create_index('ix_applicability_reviews_source_id','applicability_reviews',['source_id'])


def downgrade():
    op.drop_index('ix_applicability_reviews_source_id',table_name='applicability_reviews')
    op.drop_table('applicability_reviews')
