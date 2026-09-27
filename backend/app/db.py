from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, url: str):
        if url.startswith('sqlite:///') and ':memory:' not in url:
            Path(url.removeprefix('sqlite:///')).parent.mkdir(parents=True, exist_ok=True)
        kw = {'pool_pre_ping': True}
        if url.startswith('sqlite'):
            kw['connect_args'] = {'check_same_thread': False, 'timeout': 30}
        self.engine = create_engine(url, **kw)
        if url.startswith('sqlite'):
            @event.listens_for(self.engine, 'connect')
            def sqlite_pragmas(conn, _):
                conn.execute('PRAGMA foreign_keys=ON')
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=30000')
        self.Session = sessionmaker(self.engine, expire_on_commit=False)

    def create_all(self):
        from . import models  # noqa: F401
        Base.metadata.create_all(self.engine)
