"""Explicit authorized lexical source index; no automatic content backfill."""
from alembic import op
import sqlalchemy as sa
revision='0017_source_search'
down_revision='0016_evidence_context'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('source_search_indexes',
        sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id',ondelete='CASCADE'),primary_key=True),
        sa.Column('revision',sa.String(64),nullable=False),
        sa.Column('index_version',sa.String(80),nullable=False),
        sa.Column('search_text',sa.Text(),nullable=False),
        sa.Column('created_at',sa.Integer(),nullable=False))
    if op.get_bind().dialect.name=='postgresql':
        op.execute("CREATE INDEX ix_sources_title_fts ON sources USING gin (to_tsvector('simple', title))")
        op.execute("CREATE INDEX ix_source_search_body_fts ON source_search_indexes USING gin (to_tsvector('simple', search_text))")


def downgrade():
    if op.get_bind().dialect.name=='postgresql':
        op.drop_index('ix_sources_title_fts',table_name='sources')
    op.drop_table('source_search_indexes')
