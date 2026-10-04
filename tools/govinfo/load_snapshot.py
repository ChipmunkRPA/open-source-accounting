"""Load a hash-verified Standard section snapshot into a local search index."""
from pathlib import Path
import argparse
import gzip
import hashlib
import io
import json
import sqlite3


def shard_bytes(snapshot, doc):
    name = doc['derived_shard']
    if Path(name).name != name or not name.endswith('.jsonl.gz'):
        raise ValueError('Invalid shard path')
    parts = doc.get('derived_parts')
    if parts is None:
        path = snapshot/name
        if path.is_symlink():
            raise ValueError('Symlinked shard is not allowed')
        data = path.read_bytes()
    else:
        if not isinstance(parts, list) or not 1 <= len(parts) <= 8:
            raise ValueError('Invalid transfer-part list')
        chunks = []
        offset = 0
        for ordinal, part in enumerate(parts, 1):
            expected_name = name + f'.part{ordinal:02d}'
            if part['file'] != expected_name or part['offset'] != offset or not 0 < part['bytes'] <= 10*1024*1024:
                raise ValueError('Invalid transfer-part identity or order')
            path = snapshot/expected_name
            if path.is_symlink():
                raise ValueError('Symlinked transfer part is not allowed')
            chunk = path.read_bytes()
            if len(chunk) != part['bytes'] or hashlib.sha256(chunk).hexdigest() != part['sha256']:
                raise ValueError('Transfer part integrity mismatch')
            chunks.append(chunk)
            offset += len(chunk)
        data = b''.join(chunks)
    if len(data) != doc['derived_shard_bytes'] or hashlib.sha256(data).hexdigest() != doc['derived_shard_sha256']:
        raise ValueError('Logical compressed shard integrity mismatch')
    return data


def load(snapshot, database):
    manifest=json.loads((snapshot/'manifest.json').read_bytes())
    if manifest.get('schema')!='govinfo-ecfr-research-snapshot-1':
        raise ValueError('Unsupported corpus manifest')
    if database.exists():
        raise ValueError('Choose a new database path; existing indexes are preserved')
    database.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(database) as db:
        db.executescript('CREATE TABLE sections(id TEXT PRIMARY KEY, document_id TEXT, title INTEGER, number TEXT, heading TEXT, as_of_raw TEXT, disposition TEXT, payload TEXT);'
            'CREATE VIRTUAL TABLE section_search USING fts5(id UNINDEXED, heading, text, tokenize="unicode61");')
        count=0
        for doc in manifest['documents']:
            data=shard_bytes(snapshot,doc)
            document_count=0
            with gzip.open(io.BytesIO(data),'rt',encoding='utf-8') as stream:
                for line in stream:
                    if len(line)>8_000_000:
                        raise ValueError('Section record exceeds safe reader limit')
                    row=json.loads(line)
                    if row['disposition']!='searchable_text' or row['agent_admission'] or row['professional_review'] or not row['text']:
                        raise ValueError('Unexpected public text category or approval claim')
                    if row['source_sha256']!=doc['sha256'] or row['document_id']!=doc['document_id']:
                        raise ValueError('Section source binding mismatch')
                    if hashlib.sha256(row['text'].encode()).hexdigest()!=row['normalized_display_text_sha256']:
                        raise ValueError('Section text identity mismatch')
                    if 'embedded_copyright_notice_requires_review' in row['flags']:
                        raise ValueError('Quarantined text cannot enter the public index')
                    db.execute('INSERT INTO sections VALUES(?,?,?,?,?,?,?,?)',(row['id'],row['document_id'],row['title_number'],row['section_number'],row['heading'],row['declared_amendment_date_raw'],row['disposition'],line.strip()))
                    db.execute('INSERT INTO section_search VALUES(?,?,?)',(row['id'],row['heading'],row['text']))
                    count+=1
                    document_count+=1
            if document_count!=doc['exported_section_texts']:
                raise ValueError('Document section count mismatch')
        if count!=manifest['exported_section_texts']:
            raise ValueError('Snapshot section count mismatch')
    return count


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps({'indexed_section_texts':load(args.snapshot.resolve(),args.database.resolve())}))
