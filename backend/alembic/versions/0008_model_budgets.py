"""Atomic spend envelopes. Never authorize a budget or rewrite historical liabilities."""
from alembic import op
import sqlalchemy as sa
revision = '0008_budgets'
down_revision = '0007_attempts'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('model_budgets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('terms', sa.JSON(), nullable=False),
        sa.Column('terms_sha256', sa.String(64), nullable=False, unique=True),
        sa.Column('authorization_sha256', sa.String(64), nullable=False, unique=True),
        sa.Column('authorized_by', sa.String(128), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('limit_nanos', sa.BigInteger(), nullable=False),
        sa.Column('per_call_nanos', sa.BigInteger(), nullable=False),
        sa.Column('held_nanos', sa.BigInteger(), nullable=False),
        sa.Column('committed_nanos', sa.BigInteger(), nullable=False),
        sa.Column('revoked_at', sa.Integer()))
    with op.batch_alter_table('model_attempts') as batch:
        batch.add_column(sa.Column('budget_id', sa.String(36)))
        batch.add_column(sa.Column('reserved_nanos', sa.BigInteger()))
        batch.add_column(sa.Column('budget_state', sa.String(20)))
        batch.create_foreign_key('fk_model_attempt_budget', 'model_budgets', ['budget_id'], ['id'])
        batch.create_index('ix_model_attempts_budget_id', ['budget_id'])


def downgrade():
    with op.batch_alter_table('model_attempts') as batch:
        batch.drop_index('ix_model_attempts_budget_id')
        batch.drop_constraint('fk_model_attempt_budget', type_='foreignkey')
        batch.drop_column('budget_state')
        batch.drop_column('reserved_nanos')
        batch.drop_column('budget_id')
    op.drop_table('model_budgets')
