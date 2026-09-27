"""Crossref metadata-only works pages; no abstract, full text, crawling or rights grant."""
import json
import re
import sys
import math
from datetime import date
from urllib.parse import urlsplit, parse_qs, quote
from .sec_core.core import CoreError, digest, canonical

VERSION = 'crossref-works-1'
FIELDS = {'DOI', 'title', 'type', 'publisher', 'container-title', 'author', 'license', 'link',
          'update-to', 'update-policy', 'relation', 'issued', 'published-print', 'published-online',
          'created', 'deposited', 'indexed'}
DOI = re.compile(r'^10\.\d{4,9}/\S+$', re.I)


def query_contract(url):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname != 'api.crossref.org' or parts.username or parts.password
            or parts.port not in {None, 443} or parts.fragment or parts.path not in {'/works', '/v1/works'}):
        raise ValueError('Use an exact Crossref works-list HTTPS endpoint.')
    query = parse_qs(parts.query, keep_blank_values=True, strict_parsing=True)
    if any(len(v) != 1 for v in query.values()) or set(query) - {'select', 'rows', 'query', 'query.bibliographic', 'filter', 'cursor', 'mailto'}:
        raise ValueError('Unsupported or duplicated Crossref query parameter.')
    fields = query.get('select', [''])[0].split(',')
    if len(set(fields)) != len(fields) or set(fields) != FIELDS:
        raise ValueError('Select the exact supported bibliographic fields; abstracts are excluded.')
    rows = query.get('rows', [''])[0]
    if not rows.isdigit() or not 1 <= int(rows) <= 100:
        raise ValueError('Choose an explicit page size of 1–100 records.')
    filters = query.get('filter', [''])[0].split(',')
    if len(filters) != len(set(filters)):
        raise ValueError('Repeated scope filters are unsupported.')
    bounds = dict(f.split(':', 1) for f in filters if ':' in f)
    if (set(bounds) != {'from-pub-date', 'until-pub-date'} or len(filters) != 2
            or date.fromisoformat(bounds['from-pub-date']) > date.fromisoformat(bounds['until-pub-date'])
            or not (query.get('query', [''])[0].strip() or query.get('query.bibliographic', [''])[0].strip())):
        raise ValueError('Declare the topic and publication-date interval before discovery.')
    return {k: v[0] for k, v in query.items()}


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def bounded_tree(value, depth=0, count=None):
    count = count if count is not None else [0]
    count[0] += 1
    if count[0] > 100000 or depth > 12:
        raise ValueError('Metadata structure limit exceeded')
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in {'abstract', 'full-text', 'body', 'reference', 'assertion'}:
                raise ValueError('Non-bibliographic content is not accepted')
            bounded_tree(child, depth+1, count)
    elif isinstance(value, list):
        for child in value: bounded_tree(child, depth+1, count)
    elif isinstance(value, str) and len(value) > 10000:
        raise ValueError('Metadata string limit exceeded')
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError('Non-finite metadata number')


def string(value, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError('Invalid metadata string')
    return value


def strings(value):
    if not isinstance(value, list) or len(value) > 50:
        raise ValueError('Invalid metadata string list')
    return [string(v) for v in value]


def doi(value):
    value = string(value, 1000)
    if not DOI.fullmatch(value):
        raise ValueError('Invalid DOI')
    return value


def metadata_url(value):
    """Retain HTTP license/link metadata without upgrading it or authorizing retrieval."""
    value = string(value, 2000)
    parts = urlsplit(value)
    if (parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password
            or parts.port not in {None, 80, 443} or '\\' in value or any(c.isspace() or ord(c) < 32 for c in value)):
        raise ValueError('Invalid bibliographic URL')
    return value


def dates(value):
    if not isinstance(value, dict) or set(value)-{'date-parts', 'date-time', 'timestamp'}:
        raise ValueError('Invalid date metadata')
    parts = value.get('date-parts')
    if not isinstance(parts, list) or len(parts) != 1 or not isinstance(parts[0], list) or not 0 <= len(parts[0]) <= 3:
        raise ValueError('Invalid partial date')
    if parts[0]:
        if any(type(v) is not int for v in parts[0]): raise ValueError('Invalid date component')
        year, month, day = (parts[0]+[1, 1])[:3]
        date(year, month, day)
    return value  # Preserve precision; never turn a year-only date into January 1.


def extract(raw, base_url):
    query = query_contract(base_url)
    if len(raw) > 16_000_000: raise CoreError('Oversized metadata page')
    def invalid_constant(_): raise ValueError('Non-finite JSON number')
    data = json.loads(raw, object_pairs_hook=no_duplicate_keys, parse_constant=invalid_constant)
    bounded_tree(data)
    if (not isinstance(data, dict) or set(data)-{'status','message-type','message-version','message'}
            or data.get('status') != 'ok' or data.get('message-type') != 'work-list'):
        raise ValueError('Expected a successful Crossref works-list envelope')
    message = data['message']
    api_version = string(data.get('message-version'), 80)
    if not isinstance(message, dict) or set(message)-{'items','total-results','items-per-page','query','next-cursor','facets'}:
        raise ValueError('Unsupported works-list shape')
    works = message.get('items')
    if not isinstance(works, list) or len(works) > int(query['rows']): raise ValueError('Page exceeds declared scope')
    output, observed = [], set()
    for index, work in enumerate(works):
        if not isinstance(work, dict) or set(work)-FIELDS: raise ValueError('Unselected metadata field returned')
        identifier = doi(work.get('DOI'))
        if identifier.casefold() in observed: raise ValueError('Duplicate DOI requires page review')
        observed.add(identifier.casefold())
        titles = strings(work.get('title'))
        if not titles: raise ValueError('Missing title')
        item = {'work_id': identifier, 'url': 'https://doi.org/'+quote(identifier, safe='/'),
                'locator': f'/message/items/{index}', 'record_sha256': digest(canonical(work)),
                'metadata': work, 'status': 'unreviewed_bibliographic_candidate',
                'edition': None, 'effective_from': None, 'full_text_acquired': False,
                'reuse_authorized': False, 'authority_type': 'bibliographic_metadata_not_accounting_authority',
                'update_review_status': 'not_independently_checked'}
        string(work.get('type'))
        for key in ('publisher',):
            if key in work: string(work[key])
        if 'container-title' in work: strings(work['container-title'])
        for key in ('issued','published-print','published-online','created','deposited','indexed'):
            if key in work: dates(work[key])
        for key in ('license','link','update-to','author'):
            if key in work and (not isinstance(work[key], list) or len(work[key]) > 1000):
                raise ValueError('Invalid metadata list')
        for entry in work.get('license', []):
            if not isinstance(entry, dict) or set(entry)-{'URL','start','content-version','delay-in-days'}:
                raise ValueError('Invalid license metadata')
            metadata_url(entry.get('URL')); string(entry.get('content-version'))
            if 'start' in entry: dates(entry['start'])
        for entry in work.get('link', []):
            if not isinstance(entry, dict) or set(entry)-{'URL','content-type','content-version','intended-application'}:
                raise ValueError('Invalid full-text link metadata')
            metadata_url(entry.get('URL')); string(entry.get('content-version')); string(entry.get('intended-application'))
        for entry in work.get('update-to', []):
            if not isinstance(entry, dict) or set(entry)-{'DOI','type','label','updated','source'}:
                raise ValueError('Invalid update metadata')
            doi(entry.get('DOI')); string(entry.get('type'))
            if 'updated' in entry: dates(entry['updated'])
        for entry in work.get('author', []):
            if not isinstance(entry, dict) or set(entry)-{'given','family','name','ORCID','authenticated-orcid','sequence','affiliation'}:
                raise ValueError('Invalid author metadata')
            for key in ('given','family','name'):
                if key in entry: string(entry[key])
            if not any(key in entry for key in ('given','family','name')): raise ValueError('Unnamed author')
            if 'ORCID' in entry: metadata_url(entry['ORCID'])
            affiliations = entry.get('affiliation', [])
            if not isinstance(affiliations, list): raise ValueError('Invalid affiliations')
            for affiliation in affiliations:
                if not isinstance(affiliation, dict) or set(affiliation)-{'name','id'}:
                    raise ValueError('Invalid affiliation metadata')
                string(affiliation.get('name'))
        if 'update-policy' in work: metadata_url(work['update-policy'])
        if 'relation' in work and not isinstance(work['relation'], dict): raise ValueError('Invalid relations')
        for relations in work.get('relation', {}).values():
            if not isinstance(relations, list) or len(relations) > 1000: raise ValueError('Invalid relation list')
            for relation in relations:
                if not isinstance(relation, dict) or set(relation)-{'id','id-type','asserted-by'}:
                    raise ValueError('Invalid relation metadata')
                string(relation.get('id')); string(relation.get('id-type')); string(relation.get('asserted-by'))
        output.append(item)
    total = message.get('total-results')
    if type(total) is not int or total < len(works): raise ValueError('Invalid reported total')
    cursor = message.get('next-cursor')
    if cursor is not None: string(cursor, 10000)
    return {'adapter_version': VERSION, 'raw_sha256': digest(raw), 'base_url': base_url,
            'api_message_version': api_version,
            'items': output, 'query_scope': query, 'reported_total_results': total,
            'next_cursor': cursor, 'network_requests': 0,
            'coverage_scope': 'one exact metadata page; total-results is upstream-reported, not acquired coverage'}


def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    if sys.platform != 'darwin': resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))
    sys.stdout.buffer.write(canonical(extract(sys.stdin.buffer.read(16_000_001), sys.argv[1])))


if __name__ == '__main__': main()
