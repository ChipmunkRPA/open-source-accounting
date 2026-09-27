"""Exercise upgrade, schema parity and downgrade only on an explicitly supplied empty test DB."""
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]
url = os.environ.get('OSA_MIGRATION_TEST_DATABASE_URL', '')
if not url.startswith('postgresql+psycopg://'):
    raise SystemExit('Set OSA_MIGRATION_TEST_DATABASE_URL to an EMPTY disposable PostgreSQL database.')
engine = create_engine(url)
if inspect(engine).get_table_names():
    raise SystemExit('Refusing migration round trip: database is not empty.')
env = {**os.environ, 'DATABASE_URL': url, 'APP_ENV': 'test',
       'AUTO_CREATE_SCHEMA': 'false', 'AUTO_SEED': 'false'}
for args in [('upgrade', 'head'), ('check',), ('downgrade', 'base')]:
    subprocess.run([sys.executable, '-m', 'alembic', *args], cwd=ROOT/'backend', env=env, check=True)
    print('PASS alembic ' + ' '.join(args), flush=True)
if set(inspect(engine).get_table_names()) - {'alembic_version'}:
    raise SystemExit('Downgrade left application tables behind.')
subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT/'backend', env=env, check=True)
subprocess.run([sys.executable, '-m', 'alembic', 'check'], cwd=ROOT/'backend', env=env, check=True)
print(f'PASS re-upgrade and schema parity: {len(inspect(engine).get_table_names()) - 1} application tables')
engine.dispose()
