"""Persist spreadsheet context alongside its evidence revision."""
from alembic import op
import sqlalchemy as sa
revision='0016_evidence_context'
down_revision='0015_asu_tracking'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('evidence',sa.Column('extraction_context',sa.JSON(),nullable=False,server_default='{}'))
    with op.batch_alter_table('evidence') as batch:
        batch.alter_column('extraction_context',server_default=None)
        batch.alter_column('locator',existing_type=sa.String(160),type_=sa.Text())


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM evidence WHERE length(locator)>160')).scalar():
        raise ValueError('Cannot downgrade without losing exact evidence locators longer than 160 characters.')
    with op.batch_alter_table('evidence') as batch:
        batch.drop_column('extraction_context')
        batch.alter_column('locator',existing_type=sa.Text(),type_=sa.String(160))
