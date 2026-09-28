"""ASU filing identifiers and resumable daily corpus refresh."""
from alembic import op
import sqlalchemy as sa
revision = '0015_asu_tracking'
down_revision = '0014_intake_editions'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('asu_mentions',
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('asu_id', sa.String(7), primary_key=True),
        sa.Column('source_revision', sa.String(64), nullable=False),
        sa.Column('detected_at', sa.Integer(), nullable=False))
    op.create_table('asu_refresh',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('cursor', sa.String(36), nullable=False),
        sa.Column('upper_id', sa.String(36), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('started_at', sa.Integer()), sa.Column('completed_at', sa.Integer()),
        sa.Column('next_due', sa.Integer(), nullable=False),
        sa.Column('scanned', sa.Integer(), nullable=False),
        sa.Column('eligible', sa.Integer(), nullable=False),
        sa.Column('matches', sa.Integer(), nullable=False))


def downgrade():
    op.drop_table('asu_mentions')
    op.drop_table('asu_refresh')
