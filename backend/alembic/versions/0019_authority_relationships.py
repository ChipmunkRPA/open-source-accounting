"""Revision-bound authority assertions with independent review; no seeded approvals."""
from alembic import op
import sqlalchemy as sa
revision='0019_authority_relationships'
down_revision='0018_index_sweeps'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('authority_relationships',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id',ondelete='CASCADE'),nullable=False),
        sa.Column('target_id',sa.String(36),sa.ForeignKey('sources.id',ondelete='CASCADE'),nullable=False),
        sa.Column('relation',sa.String(20),nullable=False),
        sa.Column('revision',sa.String(64),nullable=False,unique=True),
        sa.Column('payload',sa.JSON(),nullable=False),
        sa.Column('created_by',sa.String(128),sa.ForeignKey('users.id',ondelete='SET NULL')),
        sa.Column('created_at',sa.Integer(),nullable=False),
        sa.Column('sequence',sa.Integer(),nullable=False),
        sa.Column('current_review_id',sa.String(36)))
    for key in ('source_id','target_id'):
        op.create_index('ix_authority_relationships_'+key,'authority_relationships',[key])
    op.create_table('authority_reviews',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('relationship_id',sa.String(36),sa.ForeignKey('authority_relationships.id',ondelete='CASCADE'),nullable=False),
        sa.Column('sequence',sa.Integer(),nullable=False),
        sa.Column('reviewer_id',sa.String(128),sa.ForeignKey('users.id',ondelete='SET NULL')),
        sa.Column('payload',sa.JSON(),nullable=False),
        sa.Column('payload_sha256',sa.String(64),nullable=False),
        sa.Column('created_at',sa.Integer(),nullable=False),
        sa.UniqueConstraint('relationship_id','sequence'))
    op.create_index('ix_authority_reviews_relationship_id','authority_reviews',['relationship_id'])


def downgrade():
    op.drop_table('authority_reviews')
    op.drop_table('authority_relationships')
