#!/usr/bin/env python3
"""Publish an exact new public repository snapshot using the user's authenticated gh CLI.

Does not overwrite an existing repository, convert private visibility, force-push,
read application secrets, or include local Git history. Dry-run makes no network calls.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from release_preflight import collect, ROOT, MANIFEST


def run(*args,check=True,cwd=None):
    return subprocess.run(args,cwd=cwd,text=True,capture_output=True,check=check)


def validate_snapshot(root:Path):
    manifest_path=root/MANIFEST
    if not manifest_path.is_file():raise ValueError('Run python scripts/release_preflight.py --write and review the manifest first.')
    saved=json.loads(manifest_path.read_text());current=collect(root)
    if current['findings']:raise ValueError('Publication preflight found restricted files or credential-like content. Review its report.')
    if saved['files']!=current['files']:raise ValueError('Files changed after the manifest was created. Re-run preflight and review the new snapshot.')
    return current


def check_target(owner,name):
    who=run('gh','api','user','--jq','.login').stdout.strip()
    if who.lower()!=owner.lower():raise ValueError('Authenticated gh user differs from --owner. This script only creates a repository for the authenticated personal account.')
    result=run('gh','api',f'repos/{owner}/{name}',check=False)
    if result.returncode==0:raise ValueError('Refusing an existing repository. No files, history, or visibility were changed.')
    if '404' not in result.stderr and '404' not in result.stdout:
        raise ValueError('Could not verify repository absence. Check GitHub connectivity and credentials; no publication attempted.')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner',required=True);parser.add_argument('--name',default='open-source-accounting')
    parser.add_argument('--confirm-public',action='store_true');parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}',args.owner) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}',args.name):
        parser.error('Invalid GitHub account or repository name.')
    publication_attempted=False
    try:
        snapshot=validate_snapshot(ROOT)
        if args.dry_run:
            print(json.dumps({'target':f'{args.owner}/{args.name}','visibility':'public',
              'files':len(snapshot['files']),'network_calls':0,'published':False},indent=2));return
        if not args.confirm_public:parser.error('--confirm-public is required. This publishes the listed source files to the public internet.')
        if not shutil.which('gh') or not shutil.which('git'):raise ValueError('Install GitHub CLI and Git, then run gh auth login.')
        check_target(args.owner,args.name)
        target=f'{args.owner}/{args.name}'
        with tempfile.TemporaryDirectory(prefix='open-source-accounting-public-') as tmp:
            destination=Path(tmp)
            for entry in snapshot['files']:
                rel=Path(entry['path']);out=destination/rel;out.parent.mkdir(parents=True,exist_ok=True)
                raw=(ROOT/rel).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=entry['sha256']:
                    raise ValueError('A file changed while staging. No repository was created.')
                out.write_bytes(raw)
            (destination/MANIFEST).write_text(json.dumps(snapshot,indent=2)+'\n')
            run('git','init','-b','main',cwd=tmp)
            run('git','add','--all',cwd=tmp)
            run('git','-c','user.name=Open Source Accounting contributors','-c','user.email=contributors@users.noreply.github.com',
                'commit','-m','Open Source Accounting v0.6.0: original content library and rights-aware research app',cwd=tmp)
            sha=run('git','rev-parse','HEAD',cwd=tmp).stdout.strip()
            publication_attempted=True
            run('gh','repo','create',target,'--public','--source',tmp,'--remote','origin','--push',
                '--description','Open-source accounting research workspace and original educational library. Free chat; optional hosted Agent service.')
            # Repository creation has happened at this point. Never report rollback.
            info=json.loads(run('gh','api',f'repos/{target}').stdout)
            remote=json.loads(run('gh','api',f'repos/{target}/git/ref/heads/main').stdout)
            if info.get('private') is not False or remote.get('object',{}).get('sha')!=sha:
                raise ValueError('Repository was created, but visibility/commit verification failed. Inspect it on GitHub; no rollback was attempted.')
            print(json.dumps({'published':True,'repository':info['html_url'],'commit':sha,
                              'visibility':'public','website_deployed':False},indent=2))
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        suffix=' The repository may already have been created; inspect GitHub. No rollback was attempted.' if publication_attempted else ''
        raise SystemExit(f'Publication stopped: {error}{suffix}') from error

if __name__=='__main__':main()
