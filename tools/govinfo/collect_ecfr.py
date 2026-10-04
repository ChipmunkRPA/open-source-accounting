"""Collect exact official GovInfo bulk eCFR XML; no credentials or Agent grants."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import argparse
import json
import os
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parent
TITLES = (17, 12, 26, 31, 48)
MAX_FILE_BYTES = 96 * 1024 * 1024
USER_AGENT = 'OpenSourceAccountingLibrary/0.1 (public regulatory research)'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class OfficialRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.hostname != 'www.govinfo.gov':
            raise ValueError('Refusing redirect outside official GovInfo host')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def collect(title):
    listing_path = ROOT / 'discovery' / f'ecfr-title-{title}.json'
    listing_bytes = listing_path.read_bytes()
    expected_url = f'https://www.govinfo.gov/bulkdata/ECFR/title-{title}/ECFR-title{title}.xml'
    rows = [row for row in json.loads(listing_bytes)['files'] if row.get('link') == expected_url]
    if len(rows) != 1 or rows[0].get('folder') is not False:
        raise ValueError('Expected exactly one officially listed XML container')
    row = rows[0]
    if not 0 < row['size'] <= MAX_FILE_BYTES:
        raise ValueError('Unexpected official XML container size')
    raw_dir = ROOT / 'raw'
    raw_dir.mkdir(exist_ok=True)
    receipt_path = raw_dir / f'ecfr-title-{title}.receipt.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_bytes())
        if receipt['source_listing_sha256'] != hashlib.sha256(listing_bytes).hexdigest():
            raise ValueError('Listing changed; retain this snapshot and collect into a new workspace')
        raw = ROOT / receipt['local_path']
        data = raw.read_bytes()
        if len(data) != receipt['bytes'] or hashlib.sha256(data).hexdigest() != receipt['sha256']:
            raise ValueError('Previously retained source bytes changed')
        print(json.dumps({'title': title, 'status': 'already_retained', 'bytes': len(data)}), flush=True)
        return
    request = urllib.request.Request(expected_url, headers={
        'User-Agent': USER_AGENT, 'Accept': 'application/xml', 'Accept-Encoding': 'identity'})
    partial = raw_dir / f'ecfr-title-{title}.partial'
    digest = hashlib.sha256()
    size = 0
    started = utc_now()
    with urllib.request.build_opener(OfficialRedirects()).open(request, timeout=45) as response:
        if response.status != 200 or response.headers.get_content_type() not in {'application/xml', 'text/xml'}:
            raise ValueError('Official source did not return XML')
        with partial.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise ValueError('XML container exceeded the bounded limit')
                digest.update(chunk)
                output.write(chunk)
        if size != row['size']:
            raise ValueError('Source size differs from discovery; refresh/review before accepting')
        sha = digest.hexdigest()
        relative = f'raw/{sha}.xml'
        os.replace(partial, ROOT / relative)
        receipt = {
            'schema': 'accounting-official-bulk-receipt-1', 'collection': 'ECFR', 'title': title,
            'source_url': expected_url, 'source_listing_url': f'https://www.govinfo.gov/bulkdata/json/ECFR/title-{title}',
            'source_listing_sha256': hashlib.sha256(listing_bytes).hexdigest(),
            'listed_last_modified_gmt': row['formattedLastModifiedTime'],
            'retrieval_started_at': started, 'retrieved_at': utc_now(), 'status': response.status,
            'response_content_type': response.headers.get('Content-Type'),
            'response_last_modified': response.headers.get('Last-Modified'),
            'response_etag': response.headers.get('ETag'), 'sha256': sha, 'bytes': size,
            'local_path': relative, 'downloaded_document_count': 1,
            'rights_basis_url': 'https://www.govinfo.gov/about/policies',
            'bulk_access_documentation': 'https://www.govinfo.gov/developers',
            'rights_scope': 'Official bulk research acquisition; embedded third-party components require separate filtering',
            'publicly_published': False, 'agent_admission': False, 'professional_review': False,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'title': title, 'status': 'retained', 'bytes': size, 'sha256': sha}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--discover', action='store_true')
    args = parser.parse_args()
    ROOT = args.workspace.resolve()
    ROOT.mkdir(parents=True, exist_ok=True)
    if args.discover:
        discovery = ROOT / 'discovery'
        discovery.mkdir(exist_ok=True)
        for title in TITLES:
            url = f'https://www.govinfo.gov/bulkdata/json/ECFR/title-{title}'
            request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
            with urllib.request.build_opener(OfficialRedirects()).open(request, timeout=30) as response:
                data = response.read(2_000_001)
                if response.status != 200 or len(data) > 2_000_000:
                    raise ValueError('Unexpected bulk discovery response')
                json.loads(data)
            path = discovery / f'ecfr-title-{title}.json'
            if path.exists() and path.read_bytes() != data:
                raise ValueError('Discovery changed; use a new snapshot workspace')
            path.write_bytes(data)
    for title in TITLES:
        collect(title)
