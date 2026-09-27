import json
from pathlib import Path
from ..errors import fail

CATALOG = json.loads(Path(__file__).with_name('catalog.json').read_text())
BY_ID = {row['id']: row for row in CATALOG}


def get_workflow(name, config):
    row = BY_ID.get(name)
    if not row:
        fail('WORKFLOW_NOT_FOUND', 'Unknown Agent workflow.', 404)
    if not row['enabled_by_default'] and not config.enable_experimental_agents:
        fail('FEATURE_NOT_ENABLED', 'This workflow is experimental and is not enabled by the operator.', 403)
    return row


def public_catalog(config):
    return [{**row, 'enabled': row['enabled_by_default'] or config.enable_experimental_agents}
            for row in CATALOG]
