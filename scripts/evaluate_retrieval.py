"""Run offline fixtures only; never reads credentials or accepts a live database URL."""
import argparse
import json
from pathlib import Path
from app.evaluation.retrieval import write_report, load, reviewer_packets, compare_reports

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--corpus',default='evaluation/retrieval-engineering-1.json')
parser.add_argument('--output',required=True)
parser.add_argument('--review-packets')
parser.add_argument('--baseline')
parser.add_argument('--diff-output')
args=parser.parse_args()
if bool(args.baseline)!=bool(args.diff_output):parser.error('--baseline and --diff-output must be supplied together')
result=write_report(args.corpus,args.output)
if args.review_packets:
    Path(args.review_packets).write_text(json.dumps(reviewer_packets(load(args.corpus),result),indent=2)+'\n')
print(f"{result['case_count']} engineering cases; {result['professional_adjudications']} professional adjudications; passed={result['passed']}")
for case in result['cases']:
    print(f"{case['case_id']}: precision={case['precision']} recall={case['recall']} forbidden={len(case['forbidden_units_retrieved'])} failures={case['failures']}")
passed=result['passed']
if args.baseline:
    comparison=compare_reports(json.loads(Path(args.baseline).read_text()),result)
    Path(args.diff_output).write_text(json.dumps(comparison,indent=2)+'\n')
    passed=passed and comparison['passed']
raise SystemExit(0 if passed else 1)
