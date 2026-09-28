"""Resumable explicit derived-index cleanup; no automatic schedule."""
from alembic import op
import sqlalchemy as sa
revision='0018_index_sweeps'
down_revision='0017_source_search'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('search_index_sweeps',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('cleanup_version',sa.String(80),nullable=False),
        sa.Column('request_sha256',sa.String(64),nullable=False,unique=True),
        sa.Column('actor_id',sa.String(128),nullable=False),
        sa.Column('cursor',sa.String(36),nullable=False),
        sa.Column('upper_id',sa.String(36),nullable=False),
        sa.Column('state',sa.String(20),nullable=False),
        *[sa.Column(name,sa.Integer(),nullable=False) for name in
          ('sequence','initial_stored','scanned','retained','removed','vanished','started_at')],
        sa.Column('completed_at',sa.Integer()))


def downgrade():
    op.drop_table('search_index_sweeps')
