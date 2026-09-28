"""Administrative correction queue; no source approvals or restoration."""
from alembic import op
import sqlalchemy as sa
revision='0013_corrections'
down_revision='0012_applicability'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('correction_cases',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id'),nullable=False),
        sa.Column('kind',sa.String(20),nullable=False),
        sa.Column('status',sa.String(20),nullable=False),
        sa.Column('version',sa.Integer(),nullable=False),
        sa.Column('policy_version',sa.Integer(),nullable=False),
        sa.Column('review_revision',sa.String(64),nullable=False),
        sa.Column('created_at',sa.Integer(),nullable=False))
    op.create_index('ix_correction_cases_source_id','correction_cases',['source_id'])
    op.create_table('correction_events',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('case_id',sa.String(36),sa.ForeignKey('correction_cases.id'),nullable=False),
        sa.Column('version',sa.Integer(),nullable=False),
        sa.Column('actor_id',sa.String(128),sa.ForeignKey('users.id',ondelete='SET NULL')),
        sa.Column('action',sa.String(20),nullable=False),
        sa.Column('note',sa.Text(),nullable=False),
        sa.Column('source_policy_version',sa.Integer(),nullable=False),
        sa.Column('created_at',sa.Integer(),nullable=False),
        sa.UniqueConstraint('case_id','version'))
    op.create_index('ix_correction_events_case_id','correction_events',['case_id'])


def downgrade():
    op.drop_table('correction_events')
    op.drop_table('correction_cases')
