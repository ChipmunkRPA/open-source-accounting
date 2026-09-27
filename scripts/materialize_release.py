#!/usr/bin/env python3
"""Materialize a checksummed source transport on a fresh repository checkout.

Transport only: does not deploy, use Cloud credentials, or evaluate code from
archive paths. The workflow commits the inspected native source without forcing.
"""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    transport=ROOT/'.release'
    manifest=json.loads((transport/'ready.json').read_text())
    if manifest['repository']!='ChipmunkRPA/open-source-accounting':raise SystemExit('Wrong target.')
    pieces=[]
    for piece in manifest['pieces']:
        name=piece['path']
        if not name.startswith('part-') or '/' in name:raise SystemExit('Unsafe transport path.')
        data=(transport/name).read_bytes()
        if len(data)!=piece['bytes'] or hashlib.sha256(data).hexdigest()!=piece['sha256']:raise SystemExit('Transport piece mismatch.')
        pieces.append(data)
    payload=b''.join(pieces)
    if hashlib.sha256(payload).hexdigest()!=manifest['archive_sha256']:raise SystemExit('Archive mismatch.')
    extracted={}
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:xz') as tar:
        total=0
        for member in tar:
            p=PurePosixPath(member.name)
            if (not member.isfile() or p.is_absolute() or '..' in p.parts or not p.parts
                    or p.parts[0] in {'.git','.release'} or member.name.startswith('.github/workflows/')
                    or member.name in extracted):
                raise SystemExit('Unexpected or unsafe archive member.')
            raw=tar.extractfile(member).read();total+=len(raw)
            if total>20_000_000 or len(raw)!=member.size:
                raise SystemExit('Source hash/size mismatch.')
            raw.decode('utf-8') # this transport intentionally contains text source only
            target=ROOT.joinpath(*p.parts)
            if target.exists() and (not target.is_file() or target.is_symlink() or target.read_bytes()!=raw):
                raise SystemExit(f'Refusing to overwrite an existing differing file: {member.name}')
            extracted[member.name]=raw
    if len(extracted)!=manifest['file_count']:raise SystemExit('Incomplete archive.')
    for required in manifest['required_files']:
        if required not in extracted:raise SystemExit('Required source file missing.')
    # No paths are written until every member has been checked.
    for name,raw in extracted.items():
        target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    shutil.rmtree(transport)
    print(f'Materialized {len(extracted)} verified native source files. No application/Cloud code executed.')

if __name__=='__main__':main()
