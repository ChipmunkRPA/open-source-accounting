"""User/workspace source entitlements, with one current approved grant per assignment."""
from alembic import op
import sqlalchemy as sa
revision = '0005_scopes'
down_revision = '0004_counsel'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('source_scope_grants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('subject_user_id', sa.String(128), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('proposal', sa.JSON(), nullable=False),
        sa.Column('record_sha256', sa.String(64), nullable=False),
        sa.Column('submitted_by', sa.String(128), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('submitted_at', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('approved_by', sa.String(128), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.Integer()),
        sa.Column('revoked_by', sa.String(128), sa.ForeignKey('users.id')),
        sa.Column('revoked_at', sa.Integer()),
        sa.Column('revocation_reason', sa.String(30)))
    op.create_index('ix_source_scope_grants_source_id', 'source_scope_grants', ['source_id'])
    op.create_index('uq_source_scope_active', 'source_scope_grants',
        ['source_id', 'subject_user_id', 'workspace_id'], unique=True,
        postgresql_where=sa.text("status = 'approved'"), sqlite_where=sa.text("status = 'approved'"))


def downgrade():
    op.drop_table('source_scope_grants')
