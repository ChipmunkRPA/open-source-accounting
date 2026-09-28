"""Immutable multipart inventory revisions; no implicit corpus completeness or approvals."""
from alembic import op
import sqlalchemy as sa
revision = '0014_intake_editions'
down_revision = '0013_corrections'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('intake_editions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('family_id', sa.String(80), nullable=False),
        sa.Column('collection_key', sa.String(160), nullable=False),
        sa.Column('edition', sa.String(80), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('request_sha256', sa.String(64), nullable=False),
        sa.Column('manifest', sa.JSON(), nullable=False),
        sa.Column('manifest_sha256', sa.String(64), nullable=False),
        sa.Column('created_by', sa.String(128), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.UniqueConstraint('family_id', 'collection_key', 'edition', 'revision'))


def downgrade():
    op.drop_table('intake_editions')
