"""Run synthetic fixtures in SQLite or an explicitly confirmed empty local PostgreSQL test database."""
import argparse
import os
import json
from pathlib import Path
from app.evaluation.retrieval import write_report, load, reviewer_packets, compare_reports

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--corpus',default='evaluation/retrieval-engineering-1.json')
parser.add_argument('--output',required=True)
parser.add_argument('--review-packets')
parser.add_argument('--baseline')
parser.add_argument('--diff-output')
parser.add_argument('--postgres',action='store_true',help='Use OSA_EVALUATION_POSTGRES_URL with disposable-test confirmation')
parser.add_argument('--cross-engine',action='store_true',help='Compare the same code/corpus across SQLite and PostgreSQL')
args=parser.parse_args()
if args.cross_engine and not args.baseline:parser.error('--cross-engine requires a baseline')
if bool(args.baseline)!=bool(args.diff_output):parser.error('--baseline and --diff-output must be supplied together')
postgres_url=os.environ.get('OSA_EVALUATION_POSTGRES_URL') if args.postgres else None
if args.postgres and not postgres_url:parser.error('OSA_EVALUATION_POSTGRES_URL is required')
result=write_report(args.corpus,args.output,postgres_url=postgres_url)
if args.review_packets:
    Path(args.review_packets).write_text(json.dumps(reviewer_packets(load(args.corpus),result),indent=2)+'\n')
print(f"{result['case_count']} engineering cases; {result['professional_adjudications']} professional adjudications; passed={result['passed']}")
for case in result['cases']:
    print(f"{case['case_id']}: precision={case['precision']} recall={case['recall']} forbidden={len(case['forbidden_units_retrieved'])} failures={case['failures']}")
passed=result['passed']
if args.baseline:
    comparison=compare_reports(json.loads(Path(args.baseline).read_text()),result,cross_engine=args.cross_engine)
    Path(args.diff_output).write_text(json.dumps(comparison,indent=2)+'\n')
    passed=passed and comparison['passed']
raise SystemExit(0 if passed else 1)
