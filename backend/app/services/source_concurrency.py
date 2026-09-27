"""One Crossref network request across workers, independent of request-rate slots."""
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from ..errors import fail

# Stable, provider-specific PostgreSQL session lock; never an application row ID.
CROSSREF_LOCK = 0x4F534143524546


@contextmanager
def crossref_slot(database_url):
    if database_url.startswith(('postgresql://', 'postgresql+psycopg://')):
        engine = create_engine(database_url, poolclass=NullPool)
        try:
            with engine.connect() as connection:
                locked = connection.scalar(text('SELECT pg_try_advisory_lock(:key)'), {'key': CROSSREF_LOCK})
                if not locked:
                    fail('SOURCE_BUSY', 'Another Crossref request is active; resume this attempt later.', 409)
                try:
                    yield
                finally:
                    connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': CROSSREF_LOCK})
        finally:
            engine.dispose()
    elif database_url.startswith('sqlite:///'):
        import fcntl
        path = Path(database_url.removeprefix('sqlite:///')+'.crossref.lock')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a') as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fail('SOURCE_BUSY', 'Another Crossref request is active; resume this attempt later.', 409)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    else:
        fail('SOURCE_CONFIGURATION', 'Crossref requires shared PostgreSQL or local SQLite coordination.', 503)


class CrossrefGateway:
    def __init__(self, gateway, database_url):
        self.gateway, self.database_url = gateway, database_url

    def get(self, url):
        with crossref_slot(self.database_url):
            return self.gateway.get(url)
