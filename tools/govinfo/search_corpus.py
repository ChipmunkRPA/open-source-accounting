"""Query the local immutable-snapshot section index without running a service."""
from pathlib import Path
import argparse
import json
import sqlite3


def search(database, query, *, title=None, limit=10):
    if not query.strip() or len(query) > 500 or not 1 <= limit <= 20:
        raise ValueError('Use a nonempty query of at most 500 characters and limit 1..20')
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
        sql = ('SELECT sections.payload FROM section_search JOIN sections ON sections.id=section_search.id '
               'WHERE section_search MATCH ?')
        values = [query]
        if title is not None:
            sql += ' AND sections.title=?'
            values.append(title)
        sql += ' ORDER BY rank LIMIT ?'
        values.append(limit)
        return [json.loads(row[0]) for row in db.execute(sql, values)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query')
    parser.add_argument('--title', type=int, choices=[12, 17, 26, 31, 48])
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--database', type=Path, default=Path(__file__).resolve().parent/'derived/sections.sqlite')
    args = parser.parse_args()
    try:
        results = search(args.database, args.query, title=args.title, limit=args.limit)
    except (ValueError, sqlite3.Error) as error:
        parser.exit(2, f'Cannot query corpus: {error}\n')
    print(json.dumps({'count':len(results),'results':results}, ensure_ascii=False, indent=2))
