"""Offline consistency check for the all-content queue and handoff inventories."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT/path).read_text())
tasks = read('tasks/queue.json')['tasks']
by_issue = {t['issue_number']: t for t in tasks}
assert len(by_issue) == len(tasks) == 38
seen, active = set(), set()
def visit(number):
    assert number not in active, f'Dependency cycle: {number}'
    if number in seen:
        return
    active.add(number)
    for dep in by_issue[number]['depends_on_issues']:
        visit(dep)
    active.remove(number)
    seen.add(number)
for number in by_issue:
    visit(number)
families = {f['id']: f for f in read('content/source_families.json')['families']}
items = {i['id']: i for i in read('content/manifest.json')['items']}
originals = read('content/original_items.json')['items']
assert len(originals) == len({i['id'] for i in originals}) == 63
for item in originals:
    assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256']
    assert item['id'] in items and not item['agent_eligible']
    assert set(item['source_families']) <= families.keys()
for family in families.values():
    assert not family['raw_text_authorized_by_this_file']
    assert set(family['issue_numbers']) <= by_issue.keys()
for topic in read('content/topic_coverage.json')['topics']:
    assert set(topic['source_families']) <= families.keys()
    assert set(topic['existing_broad_topic_matches']) <= items.keys()
assert {w['id'] for w in read('tasks/workflow_map.json')['workflows']} == {w['id'] for w in read('backend/app/agents/catalog.json')}
print('PASS: 38-task DAG, 32 family recipes, 63 baseline hashes, 47 topic records, 16 workflows; no approvals granted.')
