"""Export only searchable government-text projections for the Standard corpus."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json

PART_BYTES = 10 * 1024 * 1024

from index_ecfr import write_gzip_jsonl


def export(workspace, destination):
    manifest = json.loads((workspace/'derived/manifest.json').read_bytes())
    destination.mkdir(parents=True, exist_ok=True)
    total = 0
    text_hashes = set()
    for doc in manifest['documents']:
        source = workspace/'derived'/doc['derived_shard']
        if hashlib.sha256(source.read_bytes()).hexdigest() != doc['derived_shard_sha256']:
            raise ValueError('Derived shard changed before export')
        with gzip.open(source, 'rt', encoding='utf-8') as stream:
            rows = [json.loads(line) for line in stream]
        selected = [r for r in rows if r['disposition']=='searchable_text']
        if len(selected) != doc['counts']['searchable_text']:
            raise ValueError('Searchable export count does not reconcile')
        if any(not r['text'] or r['agent_admission'] or 'embedded_copyright_notice_requires_review' in r['flags'] for r in selected):
            raise ValueError('Invalid text admission in public export')
        target = destination/doc['derived_shard']
        write_gzip_jsonl(target, selected)
        doc['derived_shard_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        doc['derived_shard_bytes'] = target.stat().st_size
        if target.stat().st_size > PART_BYTES:
            data = target.read_bytes()
            parts = []
            for ordinal, start in enumerate(range(0, len(data), PART_BYTES), 1):
                part = data[start:start+PART_BYTES]
                name = target.name + f'.part{ordinal:02d}'
                (destination/name).write_bytes(part)
                parts.append({'file':name,'offset':start,'bytes':len(part),'sha256':hashlib.sha256(part).hexdigest()})
            doc['derived_parts'] = parts
            target.unlink()
        doc['exported_section_texts'] = len(selected)
        total += len(selected)
        text_hashes.update(r['normalized_display_text_sha256'] for r in selected)
    if total != manifest['counts']['searchable_text']:
        raise ValueError('Public export total does not reconcile')
    manifest['exported_section_texts'] = total
    manifest['distinct_exported_text_sha256_count'] = len(text_hashes)
    manifest['same_text_additional_source_records'] = total-len(text_hashes)
    manifest['metadata_only_records_in_export'] = 0
    manifest['quarantined_records_in_export'] = 0
    manifest['raw_xml_in_export'] = False
    manifest['sqlite_index_in_export'] = False
    manifest['publication_status'] = 'review_candidate'
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    manifest=export(args.workspace.resolve(),args.destination.resolve())
    print(json.dumps({'exported_section_texts':manifest['exported_section_texts'],'documents':manifest['downloaded_xml_documents']}))
