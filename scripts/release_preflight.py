#!/usr/bin/env python3
"""Create a bounded, credential-screened publication manifest; never include .git history.

This heuristic is not a complete secret/security audit. Review the staged file list.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST='release-manifest.json'
SKIP_DIRS={'.git','.venv','node_modules','.next','__pycache__','.pytest_cache','.ruff_cache','data','.qa-data','.terraform'}
PATTERNS={
 'private_key':re.compile(r'(?m)^-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
 'github_token':re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b'),
 'stripe_live_secret':re.compile(r'\b(?:sk|rk)_live_[A-Za-z0-9]{18,}\b'),
 'google_key':re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'),
 'aws_access_id':re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
 'credential_url':re.compile(r'https?://[^\s/:@]+:[^\s/@]{4,}@'),
}

def excluded(relative: Path):
    if any(p in SKIP_DIRS or p.endswith('.egg-info') for p in relative.parts):return True
    name=relative.name
    if name in {MANIFEST,'.coverage'} or name.endswith(('.pyc','.pid','.db','.db-shm','.db-wal','.tfstate','.tfstate.backup')):return True
    if name.startswith('.env') and name not in {'.env.example','.env.production.example'}:return True
    if name in {'terraform.tfvars','runtime.env.yaml'}:return True
    # Preserve current compact validation and library previews. Prior exports/coverage
    # are historical QA artifacts, not runtime dependencies for this source release.
    if relative.parts[:2] == ('frontend', 'dist'):return True
    if relative.parts[0]=='reports' and not {'bootstrap', 'rights', 'intake', 'runtime-rights', 'output-rights', 'counsel', 'scopes', 'amendments', 'gemini', 'model-ledger'} & set(relative.parts) and name != 'README.md' and not (name.startswith('content-') or name.startswith('library-') or name.startswith('release-') or name.startswith('sec-core-')):return True
    return False


def collect(root:Path=ROOT):
    root=root.resolve();entries=[];findings=[];skipped=0
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if excluded(rel):
            if p.is_file():skipped+=1
            continue
        if p.is_symlink():
            findings.append({'path':rel.as_posix(),'kind':'symlink'});continue
        if not p.is_file():continue
        if p.suffix.lower() in {'.pem','.key','.p12','.pfx','.ttf','.otf','.woff','.woff2'}:
            findings.append({'path':rel.as_posix(),'kind':'excluded_sensitive_or_font_file'});continue
        if p.name.lower() in {'credentials.json','service-account.json','id_rsa','id_ed25519'}:
            findings.append({'path':rel.as_posix(),'kind':'credential_filename'});continue
        if p.stat().st_size>5_000_000:
            findings.append({'path':rel.as_posix(),'kind':'oversized_publication_file'});continue
        raw=p.read_bytes()
        try:
            text=raw.decode('utf-8')
            for name,pattern in PATTERNS.items():
                if pattern.search(text):findings.append({'path':rel.as_posix(),'kind':name})
        except UnicodeDecodeError:
            if p.suffix.lower()!='.png':findings.append({'path':rel.as_posix(),'kind':'unreviewed_binary_type'})
        entries.append({'path':rel.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    return {'schema_version':1,'release':'0.7.0','files':entries,'excluded_files':skipped,
            'findings':findings,'limitation':'Heuristic publication screen, not a security audit or professional content review.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true')
    args=parser.parse_args();report=collect()
    if report['findings']:
        print(json.dumps({'result':'BLOCKED','findings':report['findings']},indent=2))
        raise SystemExit(1)
    if args.write:(ROOT/MANIFEST).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':'PASS','files':len(report['files']),'excluded_files':report['excluded_files'],
                      'sensitive_pattern_findings':0,'manifest_written':args.write,
                      'limitation':report['limitation']},indent=2))
if __name__=='__main__':main()
