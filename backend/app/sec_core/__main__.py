"""CLI: PYTHONPATH=backend python -m app.sec_core --help"""
import argparse
import json
from pathlib import Path
from .core import CorePack, CoreError


def main():
    default = Path(__file__).resolve().parents[3] / 'content' / 'sec_core'
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', default=str(default))
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('validate')
    sub.add_parser('inventory')
    search = sub.add_parser('preview', help='Unreviewed source-reading search, NOT Agent execution')
    search.add_argument('query'); search.add_argument('--family'); search.add_argument('--limit', type=int, default=12)
    ingest = sub.add_parser('stage', help='Stage excerpts in application database without approving them')
    ingest.add_argument('--author', required=True)
    downloaded = sub.add_parser('stage-snapshot', help='Reparse and stage an acquired document, without approval')
    downloaded.add_argument('--file', required=True)
    downloaded.add_argument('--raw-directory', required=True)
    downloaded.add_argument('--author', required=True)
    fetch = sub.add_parser('acquire', help='Explicit operator-controlled live intake; disabled without acknowledgment')
    fetch.add_argument('source_id'); fetch.add_argument('--as-of')
    fetch.add_argument('--output', default='./data/sec-core')
    fetch.add_argument('--rate-budget', default='./data/sec-request-budget.sqlite')
    fetch.add_argument('--acknowledge-access-policy', action='store_true')
    args = p.parse_args()
    try:
        pack = CorePack(args.directory)
        if args.command in {'validate', 'inventory'}:
            result = pack.report()
        elif args.command == 'preview':
            result = {'notice': pack.report()['notice'], 'agent_approved': False,
                      'items': pack.preview(args.query, args.limit, args.family)}
        elif args.command in {'stage', 'stage-snapshot'}:
            from ..config import Settings
            from ..db import Database
            from .integration import stage
            settings = Settings()
            if args.command == 'stage-snapshot':
                from .integration import snapshot_pack
                pack = snapshot_pack(args.file, args.raw_directory, pack)
            with Database(settings.database_url).Session() as db:
                result = stage(db, pack, args.author); db.commit()
        elif args.command == 'acquire':
            raise CoreError('Legacy acquisition cannot grant operation rights. Register the edition in '
                            'the unified intake registry, obtain independent route/operation approval, '
                            'then use python -m app.ingest acquire WORK_ID --request-key KEY.')
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ValueError, OSError, KeyError) as exc:
        raise SystemExit(f'SEC Core stopped: {exc}') from exc

if __name__ == '__main__':
    main()
