"""Frozen synthetic inventories, not publisher or professional-review evidence."""
from copy import deepcopy
import pytest
from app.models import IntakeEdition, Source
from app.sec_core.core import canonical, digest
from app.sec_core.fetch import Gateway
from app.services.storage import Storage
from test_intake_editions import BASE, body, create
from test_source_intake import ADMIN, registered, fetch, FakeGateway, RAW


def compare(client, row):
    response = client.get(BASE+'/'+row['id']+'/comparison', headers=ADMIN)
    assert response.status_code == 200, response.text
    return response.json()


def test_initial_inventory_and_access(client):
    row = create(client, body())
    route = BASE+'/'+row['id']+'/comparison'
    assert client.get(route).status_code == 403
    assert client.get(BASE+'/missing/comparison', headers=ADMIN).status_code == 404
    result = compare(client, row)
    assert result['initial_inventory'] and result['before'] is None
    assert result['after']['manifest_sha256'] == row['manifest_sha256']
    assert result['declared_counts'] == {'before': {'required': 0, 'optional': 0, 'total': 0},
                                         'after': {'required': 1, 'optional': 0, 'total': 1}}
    assert [p['key'] for p in result['parts']['added']] == ['part-1']
    assert result['combined']['status'] == 'unchanged'
    assert not result['approval_granted'] and not result['agent_eligible']


def test_scope_reduction_is_visible_not_new_acquisition(client):
    first = body(parts=[{'key': 'keep', 'label': 'Kept part'}, {'key': 'remove', 'label': 'Removed part'},
                        {'key': 'optional', 'label': 'Newly optional part'}])
    original = create(client, first)
    second = deepcopy(first)
    second.update(expected_revision=1, coverage_unit='Narrow pilot only', inventory_note='Explicit reduction; no source acquired.')
    second['parts'] = [second['parts'][0], {**second['parts'][2], 'required': False}, {'key': 'new', 'label': 'New unbound part'}]
    result = compare(client, create(client, second))
    assert result['before']['id'] == original['id']
    assert result['required_components_removed'] == ['remove']
    assert result['required_components_made_optional'] == ['optional']
    assert result['declared_counts']['before']['required'] == 3
    assert result['declared_counts']['after']['required'] == 2
    assert result['parts']['changed'] == [{'key': 'optional', 'fields': [{'field': 'required', 'before': True, 'after': False}]}]
    assert {c['field'] for c in result['scope_changes']} == {'coverage_unit', 'inventory_note'}
    assert result['parts']['removed'][0]['key'] == 'remove'
    assert result['parts']['added'][0]['key'] == 'new'
    assert result['parts']['unchanged_count'] == 1


def test_delivery_and_selected_hash_changes_are_frozen(client, monkeypatch):
    work = registered(client); fetch(client, work)
    first = create(client, body(work, digest(RAW)))
    new_raw = RAW.replace(b'original', b'changed')
    fetch(client, work, FakeGateway(new_raw), key='new-delivery')
    second = create(client, body(work, digest(new_raw), expected_revision=1))
    monkeypatch.setattr(Storage, 'get', lambda *_: pytest.fail('No storage reads'))
    monkeypatch.setattr(Storage, 'get_bounded', lambda *_: pytest.fail('No storage reads'))
    monkeypatch.setattr(Gateway, 'get', lambda *_: pytest.fail('No network'))
    before = compare(client, second)
    fields = {f['field']: f for f in before['parts']['changed'][0]['fields']}
    assert fields['expected_raw_sha256'] == {'field': 'expected_raw_sha256', 'before': digest(RAW), 'after': digest(new_raw)}
    assert fields['known_raw_sha256']['before'] == [digest(RAW)]
    assert fields['known_raw_sha256']['after'] == sorted([digest(RAW), digest(new_raw)])
    # Later policy changes do not fabricate a different historical comparison.
    with client.app.state.db.Session() as db:
        source = db.get(Source, work['source_id']); source.enabled = False; db.commit()
    create(client, body(work, digest(new_raw), expected_revision=2, inventory_note='A later declaration does not rewrite prior comparison.'))
    assert compare(client, second) == before
    assert compare(client, first)['initial_inventory']


def test_combined_is_separate_and_reorder_is_explicit(client):
    first = body(parts=[{'key': 'a', 'label': 'Alpha'}, {'key': 'b', 'label': 'Beta'}])
    create(client, first)
    second = deepcopy(first); second.update(expected_revision=1, combined={'key': 'combined', 'label': 'Separate combined'})
    second['parts'].reverse()
    result = compare(client, create(client, second))
    assert result['parts']['changed'] == [] and result['parts']['unchanged_count'] == 2
    assert result['parts']['order_before'] == ['a', 'b'] and result['parts']['order_after'] == ['b', 'a']
    assert result['parts']['order_changed'] and result['combined']['status'] == 'added'
    assert result['declared_counts']['before'] == result['declared_counts']['after']
    third = deepcopy(second); third.update(expected_revision=2, combined=None)
    assert compare(client, create(client, third))['combined']['status'] == 'removed'


@pytest.mark.parametrize('broken', ['missing', 'foreign', 'skip', 'self', 'first-has-parent', 'tampered-parent', 'tampered-current'])
def test_broken_or_tampered_history_fails_closed(client, broken):
    first = create(client, body())
    second = create(client, body(expected_revision=1))
    foreign = create(client, body(collection_key='different-collection'))
    third = create(client, body(expected_revision=2))
    target = third if broken == 'skip' else first if broken == 'first-has-parent' else second
    with client.app.state.db.Session() as db:
        row = db.get(IntakeEdition, target['id'])
        if broken in {'tampered-parent', 'tampered-current'}:
            row = db.get(IntakeEdition, first['id'] if broken == 'tampered-parent' else second['id'])
            row.manifest = {**row.manifest, 'inventory_note': 'Unauthorized mutation'}
        else:
            parent = {'missing': 'missing', 'foreign': foreign['id'], 'skip': first['id'],
                      'self': second['id'], 'first-has-parent': foreign['id']}[broken]
            row.manifest = {**row.manifest, 'previous_id': parent}
            row.manifest_sha256 = digest(canonical(row.manifest))
        db.commit()
    assert client.get(BASE+'/'+target['id']+'/comparison', headers=ADMIN).status_code == 409
