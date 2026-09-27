"""Durable non-content inference attempts; never backfill invented usage."""
from alembic import op
import sqlalchemy as sa

revision = '0007_attempts'
down_revision = '0006_amendments'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('runs', sa.Column('execution_id', sa.String(36)))
    op.create_table('model_attempts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('operation_key', sa.String(64), nullable=False, unique=True),
        sa.Column('user_id', sa.String(128), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id', ondelete='SET NULL')),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('runs.id', ondelete='SET NULL')),
        sa.Column('chat_id', sa.String(36), sa.ForeignKey('chats.id', ondelete='SET NULL')),
        sa.Column('run_revision', sa.Integer()),
        sa.Column('execution_id', sa.String(36)),
        sa.Column('phase', sa.String(30), nullable=False),
        sa.Column('provider', sa.String(30), nullable=False),
        sa.Column('project', sa.String(30), nullable=False),
        sa.Column('location', sa.String(20), nullable=False),
        sa.Column('model_id', sa.String(80), nullable=False),
        sa.Column('model_version', sa.String(128)),
        sa.Column('prompt_version', sa.String(80), nullable=False),
        sa.Column('thinking', sa.String(10), nullable=False),
        sa.Column('output_limit', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.Integer(), nullable=False),
        sa.Column('finished_at', sa.Integer()),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('error_code', sa.String(80)),
        sa.Column('http_status', sa.Integer()),
        sa.Column('usage', sa.JSON(none_as_null=True)),
        sa.Column('cost_state', sa.String(20), nullable=False),
        sa.Column('cost_estimate', sa.JSON(none_as_null=True)))
    op.create_index('ix_model_attempts_run_id', 'model_attempts', ['run_id'])
    op.create_index('ix_model_attempts_started_at', 'model_attempts', ['started_at'])


def downgrade():
    op.drop_table('model_attempts')
    op.drop_column('runs', 'execution_id')
