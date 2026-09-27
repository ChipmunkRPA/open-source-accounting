#!/usr/bin/env python3
"""Publish a reviewed local release into the existing project; never force push.

Run from a release checkout after `gh auth login`. The default is a local
preview; pass --apply after reviewing the listed files. This script only targets
ChipmunkRPA/open-source-accounting and never modifies unrelated repositories.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

REPO = 'ChipmunkRPA/open-source-accounting'
ALLOWED_ROOTS = {'backend', 'frontend', 'content', 'docs', 'infra', 'scripts', 'tests', 'fixtures', 'reports', '.github'}
ALLOWED_ROOT_FILES = {'readme.md', 'README.md', 'progress.md', 'PUBLISHING.md', 'LICENSE', 'NOTICE.md', 'SECURITY.md', 'CONTRIBUTING.md', 'license-notice.md', 'Dockerfile', 'compose.yaml', 'Makefile', '.dockerignore', '.gitignore'}
DENIED_PARTS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.next', 'data', 'uploads', 'secrets', 'credentials'}
DENIED_SUFFIXES = {'.pyc', '.db', '.sqlite', '.sqlite3', '.pem', '.key', '.p12', '.pfx'}


def run(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return proc.stdout.strip()


def publication_files(root: Path) -> list[tuple[Path, str]]:
    result = []
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        if any(p in DENIED_PARTS for p in rel.parts):
            continue
        if rel.parts[0] not in ALLOWED_ROOTS and rel.as_posix() not in ALLOWED_ROOT_FILES:
            continue
        if path.suffix.lower() in DENIED_SUFFIXES:
            continue
        if path.name == '.env' or (path.name.startswith('.env.') and not path.name.endswith(('.example', '.sample'))):
            continue
        if path.stat().st_size > 10_000_000:
            raise RuntimeError(f'Refusing large file: {rel}')
        result.append((path, rel.as_posix()))
    if not any(rel == 'backend/app/main.py' for _, rel in result):
        raise RuntimeError('Expected source tree not found; run from the full release checkout.')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Create a local commit and push it without force.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    for executable in ('git', 'gh'):
        if not shutil.which(executable):
            raise SystemExit(f'Install {executable} first.')
    account = run('gh', 'api', 'user', '--jq', '.login')
    if account != 'ChipmunkRPA':
        raise SystemExit(f'Wrong GitHub account: {account}; expected ChipmunkRPA.')
    repo = json.loads(run('gh', 'api', f'repos/{REPO}'))
    if repo.get('private') is not False or repo.get('archived'):
        raise SystemExit('Target must already be public and unarchived; this script will not change visibility.')
    if not repo.get('permissions', {}).get('push'):
        raise SystemExit('The authenticated account needs push permission.')
    branch = repo.get('default_branch', 'main')
    # This scan is a safeguard, not a guarantee that all secrets are detectable.
    subprocess.run(['python3', str(root / 'scripts/release_preflight.py'), '--check'], cwd=root, check=True)
    selected = publication_files(root)
    print(f'Repository: {REPO}; branch: {branch}; files: {len(selected)}')
    for path, rel in selected:
        print(hashlib.sha256(path.read_bytes()).hexdigest(), rel)
    if not args.apply:
        print('\nPREVIEW ONLY. Review the files above, then repeat with --apply.')
        return
    with tempfile.TemporaryDirectory(prefix='open-source-accounting-publish-') as tmp:
        dest = Path(tmp) / 'repository'
        run('gh', 'repo', 'clone', REPO, str(dest), '--', '--branch', branch, '--single-branch')
        run('git', 'config', 'user.name', account, cwd=dest)
        run('git', 'config', 'user.email', '154071180+ChipmunkRPA@users.noreply.github.com', cwd=dest)
        # Match the protected bootstrap snapshot, or stop rather than overwrite
        # code someone else has since published.
        if (dest / 'backend/app/main.py').exists():
            raise SystemExit('Repository already contains an application. Use a reviewed pull request instead.')
        allowed_bootstrap_files = {'.gitignore', 'README.md', 'readme.md', 'progress.md', 'LICENSE', 'PUBLICATION_STATUS.md'}
        for tracked in run('git', 'ls-files', cwd=dest).splitlines():
            if tracked in allowed_bootstrap_files or tracked.startswith('.release/') or tracked == '.github/workflows/import-source.yml' or tracked == '.github/workflows/cleanup-incomplete-import.yml':
                continue
            raise SystemExit(f'Unexpected existing file: {tracked}. Review it before publication.')
        # Clear this attempt's temporary transport objects, not repository history.
        shutil.rmtree(dest / '.release', ignore_errors=True)
        for name in ('import-source.yml', 'cleanup-incomplete-import.yml'):
            (dest / '.github/workflows' / name).unlink(missing_ok=True)
        (dest / 'PUBLICATION_STATUS.md').unlink(missing_ok=True)
        if (root / 'readme.md').exists():
            (dest / 'README.md').unlink(missing_ok=True)
        for source, rel in selected:
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        run('git', 'add', '--all', cwd=dest)
        run('git', 'diff', '--cached', '--check', cwd=dest)
        run('git', 'commit', '-m', 'Publish open-source-accounting v0.6: content pack and mandatory MFA', cwd=dest)
        # Remote concurrent updates cause an ordinary non-fast-forward rejection.
        run('git', 'push', 'origin', f'HEAD:{branch}', cwd=dest)
        local = run('git', 'rev-parse', 'HEAD', cwd=dest)
        remote = run('gh', 'api', f'repos/{REPO}/commits/{branch}', '--jq', '.sha')
        if remote != local:
            raise RuntimeError('Remote commit differs; do not mark publication complete until reconciled.')
        print(f'VERIFIED PUBLIC COMMIT: https://github.com/{REPO}/commit/{local}')
        print('GitHub publication does not deploy the application or enable live MFA in Google Cloud.')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print((exc.stderr or str(exc)).strip())
        raise SystemExit(1) from exc
