"""Operator-only local CLI. Access to the production database is privileged.

Usage: python -m app.admin set-role USER_ID admin
       python -m app.admin import-source ./reviewed-original.json --author USER_ID
Import does not approve a source; a different rights approver must approve it.
"""
import argparse
import json
from pathlib import Path
from .config import Settings
from .db import Database
from .models import User, Source, Audit
from .schemas import SourceCreate

def main():
    parser=argparse.ArgumentParser()
    commands=parser.add_subparsers(dest='command',required=True)
    role=commands.add_parser('set-role');role.add_argument('user_id');role.add_argument('role',choices=['member','admin','rights_approver','technical_reviewer'])
    source=commands.add_parser('import-source');source.add_argument('path');source.add_argument('--author',required=True)
    args=parser.parse_args();settings=Settings();database=Database(settings.database_url)
    with database.Session() as db:
        if args.command=='set-role':
            user=db.get(User,args.user_id)
            if not user:raise SystemExit('User not found. Create and verify the account first.')
            user.role=args.role
            db.add(Audit(actor_id='operator-cli',action='role.changed',target_id=user.id,detail={'role':args.role}))
            db.commit();print('Role assigned. Keep database/operator access restricted.')
        else:
            author=db.get(User,args.author)
            if not author or author.role not in {'admin','rights_approver'}:raise SystemExit('Source author must be an existing administrator.')
            path=Path(args.path)
            if path.stat().st_size>2*1024*1024:raise SystemExit('Import file is too large.')
            payload=SourceCreate.model_validate_json(path.read_text())
            row=Source(**payload.model_dump(mode='json'),created_by=author.id,reviewed=False)
            db.add(row);db.flush()
            db.add(Audit(actor_id=author.id,action='source.imported_unapproved',target_id=row.id))
            db.commit();print(json.dumps({'source_id':row.id,'status':'awaiting_independent_approval'}))
if __name__=='__main__':main()
