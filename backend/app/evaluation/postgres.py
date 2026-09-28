"""Local disposable PostgreSQL evaluation. Never writes to an existing application schema."""
import os
import re
from contextlib import contextmanager
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from ..db import Database

LOCK_ID=649316070


def validated_url(value):
    if os.environ.get('OSA_DISPOSABLE_TEST_DATABASE')!='true':
        raise ValueError('Explicit disposable-test database confirmation is required')
    url=make_url(value)
    if url.drivername!='postgresql+psycopg' or not re.fullmatch(r'osa_eval_[a-z0-9_]{1,40}',url.database or ''):
        raise ValueError('Use a dedicated PostgreSQL database named osa_eval_<test name>')
    if url.host not in (None,'localhost','127.0.0.1','::1'):
        raise ValueError('Evaluation only supports local PostgreSQL')
    if set(url.query)-{'host','port'}:
        raise ValueError('Connection overrides are not supported')
    host=url.query.get('host')
    if host and (not isinstance(host,str) or not host.startswith('/') or ',' in host):
        raise ValueError('Only a local Unix socket directory is accepted as a host override')
    return url


def require_empty(connection):
    unexpected=connection.execute(text("""SELECT EXISTS(
        SELECT 1 FROM pg_namespace WHERE nspname NOT IN ('public','information_schema') AND nspname NOT LIKE 'pg_%'
        UNION ALL SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'
        UNION ALL SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public'
        UNION ALL SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='public')""")).scalar()
    if unexpected:raise ValueError('Refusing evaluation: the dedicated database is not empty')


@contextmanager
def isolated_postgres(value):
    url=validated_url(value)
    engine=create_engine(url,isolation_level='AUTOCOMMIT')
    try:
        with engine.connect() as control:
            if not control.execute(text('SELECT pg_try_advisory_lock(:key)'),{'key':LOCK_ID}).scalar():
                raise ValueError('Another evaluation owns this disposable database')
            schemas=[]
            try:
                require_empty(control)
                version=control.execute(text('SHOW server_version')).scalar()
                @contextmanager
                def case_database(index):
                    # Only generated identifiers enter DDL; no caller-provided schema or SQL.
                    schema='osa_eval_'+uuid4().hex
                    control.execute(text('CREATE SCHEMA "'+schema+'"'));schemas.append(schema)
                    scoped=url.update_query_dict({'options':'-csearch_path='+schema})
                    db=Database(scoped.render_as_string(hide_password=False))
                    try:
                        db.create_all()
                        yield db
                    finally:
                        db.engine.dispose()
                        control.execute(text('DROP SCHEMA "'+schema+'" CASCADE'));schemas.remove(schema)
                yield case_database,version
            finally:
                # Preserve any foreign objects. Cleanup touches only schemas created by this run.
                for schema in schemas:
                    control.execute(text('DROP SCHEMA "'+schema+'" CASCADE'))
                control.execute(text('SELECT pg_advisory_unlock(:key)'),{'key':LOCK_ID})
    finally:engine.dispose()
