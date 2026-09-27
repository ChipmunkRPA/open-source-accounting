from alembic import context
from sqlalchemy import create_engine, pool
from app.config import Settings
from app.models import Base

settings = Settings()
if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=Base.metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    connectable = create_engine(settings.database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata,
                          compare_type=True, render_as_batch=connection.dialect.name == 'sqlite')
        with context.begin_transaction():
            context.run_migrations()
