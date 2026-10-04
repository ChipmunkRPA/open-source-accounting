"""Build a dated section-level research index from retained official XML.

Documents, section elements, substantive passages and searchable text are separate
counts. This never grants third-party Source rights or Agent admission.
"""
from pathlib import Path
from datetime import datetime, timezone
import collections
import argparse
import gzip
import hashlib
import json
import re
import sqlite3
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
VERSION = 'govinfo-ecfr-research-snapshot-1'
COPYRIGHT_NOTICE = re.compile(
    r'©|\bcopyright\s*(?:\(c\)|[12][0-9]{3})|all rights reserved|'
    r'\bcopyright\b.{0,80}\b(?:held|owned|reserved|retained)\b|'
    r'(?:reprinted|reproduced)\s+(?:with|by)\s+permission', re.I)
EXTERNAL_STANDARD = re.compile(r'incorporat(?:ed|ion) by reference', re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def normalized_text(element):
    """Readable text projection. Source XML remains the fidelity reference."""
    blocks = []
    for child in element:
        text = ' '.join(' '.join(child.itertext()).split())
        if text:
            blocks.append(text)
    return '\n\n'.join(blocks)


def section_rows(root, receipt):
    document_id = f"govinfo-ecfr-title-{receipt['title']}-{receipt['sha256'][:16]}"
    seen_ids = set()
    node_counts = collections.Counter(x.get('NODE') for x in root.iter() if x.get('TYPE') == 'SECTION')
    for volume_index, volume in enumerate(root.iter('ECFRBRWS'), 1):
        as_of = ' '.join(volume.findtext('AMDDATE', '').split())
        title_node = next((x for x in volume if x.get('TYPE') == 'TITLE'), None)
        if title_node is None or not as_of:
            raise ValueError('Missing volume identity or declared amendment date')
        for ordinal, section in enumerate((x for x in volume.iter() if x.get('TYPE') == 'SECTION'), 1):
            number = section.get('N')
            node = section.get('NODE')
            heading = ' '.join(section.findtext('HEAD', '').split())
            if not number or not node or not heading:
                raise ValueError('A section lacks its official identity')
            xml = ET.tostring(section, encoding='utf-8')
            text = normalized_text(section)
            section_id = f"ecfr-t{receipt['title']}-" + digest(canonical([node, number, volume_index]).encode())[:24]
            if section_id in seen_ids:
                raise ValueError('Duplicate composite section identity')
            seen_ids.add(section_id)
            body = '\n\n'.join(text.split('\n\n')[1:])
            graphics = any(x.tag.lower() in {'img', 'graphic', 'gph'} for x in section.iter())
            tables = any(x.tag in {'TABLE', 'MATH'} for x in section.iter())
            notice = bool(COPYRIGHT_NOTICE.search(text))
            reserved = '[reserved]' in heading.lower()
            substantive = bool(body.strip()) and not reserved
            flags = []
            if notice:
                flags.append('embedded_copyright_notice_requires_review')
            if EXTERNAL_STANDARD.search(text):
                flags.append('external_incorporated_material_not_acquired')
            if node_counts[node] > 1:
                flags.append('official_node_reused_use_composite_locator')
            if graphics:
                flags.append('external_graphics_not_acquired')
            if tables:
                flags.append('tabular_or_math_layout_requires_xml_view')
            disposition = 'rights_quarantine' if notice else ('searchable_text' if substantive else 'metadata_only')
            # Repeated NODE attributes cannot silently overwrite a distinct provision.
            row = {
                'schema': VERSION, 'id': section_id, 'document_id': document_id,
                'unit_kind': 'regulatory_section', 'title_number': receipt['title'],
                'section_number': number, 'heading': heading, 'official_node': node,
                'volume_ordinal': volume_index, 'section_ordinal_in_volume': ordinal,
                'volume_heading': ' '.join(title_node.findtext('HEAD', '').split()),
                'declared_amendment_date_raw': as_of,
                'source_url': receipt['source_url'], 'source_sha256': receipt['sha256'],
                'retrieved_at': receipt['retrieved_at'],
                'listed_last_modified_gmt': receipt['listed_last_modified_gmt'],
                'xml_locator': {'tag': section.tag, 'node': node, 'number': number, 'volume_ordinal': volume_index},
                'normalized_section_xml_sha256': digest(xml),
                'normalized_display_text_sha256': digest(text.encode()),
                'original_article': False, 'separate_source_publication': False,
                'substantive_text': substantive, 'reserved_heading': reserved,
                'disposition': disposition, 'rights_basis': 'US government regulatory text; third-party notices filtered',
                'rights_policy_url': 'https://www.govinfo.gov/about/policies',
                'flags': flags, 'professional_review': False, 'agent_admission': False,
                'full_visual_fidelity_verified': False,
                'text_projection': 'Whitespace-normalized XML child blocks; consult official XML for tables, formulas and images',
                'text': text if disposition == 'searchable_text' else None,
            }
            yield row


def write_gzip_jsonl(path, records):
    # Stable compressed bytes for unchanged records.
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as output:
            for row in records:
                output.write((canonical(row) + '\n').encode())


def build():
    output = ROOT / 'derived'
    output.mkdir(exist_ok=True)
    database = output / 'sections.sqlite'
    db = sqlite3.connect(database)
    db.executescript('DROP TABLE IF EXISTS section_search; DROP TABLE IF EXISTS sections;'
        'CREATE TABLE sections(id TEXT PRIMARY KEY, document_id TEXT, title INTEGER, number TEXT, heading TEXT, as_of_raw TEXT, disposition TEXT, payload TEXT);'
        'CREATE VIRTUAL TABLE section_search USING fts5(id UNINDEXED, heading, text, tokenize="unicode61");')
    summary = collections.Counter()
    documents = []
    corpus_ids = set()
    searchable_text_hashes = set()
    for receipt_path in sorted((ROOT / 'raw').glob('*.receipt.json')):
        receipt = json.loads(receipt_path.read_bytes())
        raw = (ROOT / receipt['local_path']).read_bytes()
        if len(raw) != receipt['bytes'] or digest(raw) != receipt['sha256']:
            raise ValueError('Retained source identity mismatch')
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
            raise ValueError('DTD/entity-bearing XML requires a separate safe parser decision')
        root = ET.fromstring(raw)
        rows = list(section_rows(root, receipt))
        counts = collections.Counter()
        for row in rows:
            if row['id'] in corpus_ids:
                raise ValueError('Cross-container section identity collision')
            corpus_ids.add(row['id'])
            counts['section_elements'] += 1
            counts[row['disposition']] += 1
            counts['reserved_headings'] += int(row['reserved_heading'])
            counts['substantive_sections'] += int(row['substantive_text'])
            counts['sections_with_missing_graphics'] += int('external_graphics_not_acquired' in row['flags'])
            counts['sections_with_tables_or_math'] += int('tabular_or_math_layout_requires_xml_view' in row['flags'])
            db.execute('INSERT INTO sections VALUES(?,?,?,?,?,?,?,?)', (row['id'],row['document_id'],row['title_number'],row['section_number'],row['heading'],row['declared_amendment_date_raw'],row['disposition'],canonical(row)))
            if row['disposition'] == 'searchable_text':
                searchable_text_hashes.add(row['normalized_display_text_sha256'])
                db.execute('INSERT INTO section_search VALUES(?,?,?)',(row['id'],row['heading'],row['text']))
        shard = output / f"ecfr-title-{receipt['title']}.jsonl.gz"
        write_gzip_jsonl(shard, rows)
        public_metadata = {k: v for k, v in receipt.items() if k not in {'local_path'}}
        public_metadata.update({'document_id': rows[0]['document_id'], 'counts': dict(counts),
            'amendment_dates_raw': sorted(set(row['declared_amendment_date_raw'] for row in rows)),
            'derived_shard': shard.name, 'derived_shard_sha256': digest(shard.read_bytes()),
            'derived_shard_bytes': shard.stat().st_size,
            'raw_xml_retained_locally_only': True})
        documents.append(public_metadata)
        summary.update(counts)
        print(json.dumps({'title':receipt['title'],'counts':dict(counts)}),flush=True)
    db.commit()
    indexed = db.execute('SELECT count(*) FROM section_search').fetchone()[0]
    if indexed != summary['searchable_text']:
        raise ValueError('Search index count does not reconcile')
    examples = []
    for query in ['materiality','revenue','income tax','internal control','cost accounting']:
        hits = db.execute('SELECT id,heading FROM section_search WHERE section_search MATCH ? ORDER BY rank LIMIT 3',(query,)).fetchall()
        examples.append({'query':query,'hits':[{'id':a,'heading':b} for a,b in hits]})
    db.close()
    manifest = {'schema':VERSION,'built_at':datetime.now(timezone.utc).isoformat(),
        'downloaded_xml_documents':len(documents),'source_bytes':sum(x['bytes'] for x in documents),
        'counts':dict(summary),'original_article_count':0,'live_website_ingested_count':0,
        'agent_admitted_count':0,'professional_approved_count':0,
        'distinct_searchable_text_sha256_count':len(searchable_text_hashes),
        'same_text_additional_source_records':summary['searchable_text']-len(searchable_text_hashes),
        'snapshot_is_current_law_claim':False,'documents':documents,'search_checks':examples,
        'limits':['Amendment dates are per volume and distinct from listing/download dates.',
            'Section units are not separate source publications or original articles.',
            'Metadata-only/reserved and copyright-quarantined units have no searchable body.',
            'External graphics and incorporated proprietary documents were not downloaded.',
            'Machine text projection does not verify visual, accounting or legal correctness.',
            'Local index and derived artifacts are not a deployed website or Agent grant.']}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'documents':len(documents),'counts':dict(summary),'source_bytes':manifest['source_bytes']}),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.workspace.resolve()
    build()
