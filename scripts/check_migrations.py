"""Exercise upgrade, schema parity and downgrade only on an explicitly supplied empty test DB."""
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
url = os.environ.get('OSA_MIGRATION_TEST_DATABASE_URL', '')
if not url.startswith('postgresql+psycopg://'):
    raise SystemExit('Set OSA_MIGRATION_TEST_DATABASE_URL to an EMPTY disposable PostgreSQL database.')
engine = create_engine(url)
if inspect(engine).get_table_names():
    raise SystemExit('Refusing migration round trip: database is not empty.')
env = {**os.environ, 'DATABASE_URL': url, 'APP_ENV': 'test',
       'AUTO_CREATE_SCHEMA': 'false', 'AUTO_SEED': 'false'}
# Synthetic ledger at the last pre-amendment schema. Verify preservation in CI,
# not only that a completely empty schema reaches head. The empty-DB guard above
# ensures these fixtures can never be inserted into an operator's existing database.
subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', '0005_scopes'], cwd=ROOT/'backend', env=env, check=True)
with engine.begin() as connection:
    connection.execute(text("INSERT INTO source_output_budgets (group_id, limits_sha256, released_chars) VALUES (:g, :h, 7)"),
                       {'g': 'synthetic-migration-fixture', 'h': 'a'*64})
    connection.execute(text("INSERT INTO source_output_releases (group_id, payload_sha256, character_count, created_at) VALUES (:g, :h, 7, 1234)"),
                       {'g': 'synthetic-migration-fixture', 'h': 'b'*64})
subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', '0007_attempts'], cwd=ROOT/'backend', env=env, check=True)
with engine.begin() as connection:
    connection.execute(text("""INSERT INTO model_attempts
        (id, operation_key, phase, provider, project, location, model_id, prompt_version,
         thinking, output_limit, started_at, outcome, cost_state)
        VALUES ('synthetic-legacy-attempt', :key, 'planning', 'google_cloud', 'legacy-migration',
                'us', 'gemini-3.8-flash', 'synthetic', 'MEDIUM', 2500, 1234, 'pending', 'unknown')"""), {'key': 'c'*64})
for args in [('upgrade', 'head'), ('check',), ('downgrade', 'base')]:
    subprocess.run([sys.executable, '-m', 'alembic', *args], cwd=ROOT/'backend', env=env, check=True)
    if args == ('upgrade', 'head'):
        with engine.connect() as connection:
            budget = connection.execute(text("SELECT limits_sha256, released_chars, terms_revision FROM source_output_budgets WHERE group_id=:g"),
                                        {'g': 'synthetic-migration-fixture'}).one()
            receipt = connection.execute(text("SELECT payload_sha256, character_count, created_at FROM source_output_releases WHERE group_id=:g"),
                                         {'g': 'synthetic-migration-fixture'}).one()
            if tuple(budget) != ('a'*64, 7, 1) or tuple(receipt) != ('b'*64, 7, 1234):
                raise SystemExit('Upgrade changed an existing output counter, hash or receipt.')
            legacy = connection.execute(text("SELECT cost_state, budget_id, reserved_nanos, budget_state FROM model_attempts WHERE id='synthetic-legacy-attempt'")).one()
            if tuple(legacy) != ('unknown', None, None, None) or connection.execute(text('SELECT count(*) FROM model_budgets')).scalar() != 0:
                raise SystemExit('Upgrade invented a budget or changed an unknown model liability.')
        print('PASS legacy model liability preserved without funding authorization', flush=True)
        print('PASS existing output ledger preserved across upgrade', flush=True)
    print('PASS alembic ' + ' '.join(args), flush=True)
if set(inspect(engine).get_table_names()) - {'alembic_version'}:
    raise SystemExit('Downgrade left application tables behind.')
subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT/'backend', env=env, check=True)
subprocess.run([sys.executable, '-m', 'alembic', 'check'], cwd=ROOT/'backend', env=env, check=True)
print(f'PASS re-upgrade and schema parity: {len(inspect(engine).get_table_names()) - 1} application tables')
engine.dispose()
