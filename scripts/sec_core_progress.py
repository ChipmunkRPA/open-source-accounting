#!/usr/bin/env python3
"""Render SEC seed coverage and ordered backlog without inflating acquisition/review status."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app.sec_core.core import CorePack, read_json
START = '<!-- SEC-CORE:START -->'
END = '<!-- SEC-CORE:END -->'


def render():
    report = CorePack(ROOT/'content/sec_core').report()
    queue = read_json(ROOT/'content/sec_core/work_queue.json')
    if queue['automatic_execution_enabled'] is not False:
        raise ValueError('Build backlog must not claim autonomous execution')
    lines = [START, '', '## SEC source development — 0.7.0, September 27, 2026', '',
        '**Current slice:** source-reading preview, explicit intake commands, exact locators, and integration with the existing review gates. SEC Core is not complete.', '',
        f"**{report['sources_inventoried']} source targets; {report['sources_with_excerpts']} sources with selected excerpts; {report['selected_excerpts']} excerpts ({report['excerpt_words']:,} words).**", '',
        'Zero complete source documents, zero original HTTP artifacts, zero independently reviewed sources, and zero Agent-approved SEC passages in the shipped seed. Transcribed official-source excerpts are not raw downloads. Original educational content counts remain separate.', '',
        '| Collection | Inventoried targets | Sources excerpted | Excerpts | Complete documents | Agent approved |',
        '|---|---:|---:|---:|---:|---:|']
    for row in report['families']:
        lines.append('| '+row['family']+' | '+' | '.join(str(row[k]) for k in ['inventoried','excerpted','excerpts','full_documents','agent_approved'])+' |')
    lines += ['', 'Catalog target units overlap and vary in size; these counts are not a percentage of all SEC coverage. Successfully parsing a source does not establish technical accuracy or effective dates.', '',
        '### Ordered work queue', '', '| Position | Workstream | State | Dependency |', '|---:|---|---|---|']
    for item in sorted(queue['items'], key=lambda x:x['position']):
        lines.append(f"| {item['position']} | [{item['id']} #{item['issue']}]({item['url']}) | {item['state']} | {', '.join(item['depends_on']) or 'None'} |")
    lines += ['', '**Queued means a GitHub development issue, not unattended execution.** No scheduled crawler, cloud job, future delivery or billing action was enabled.', '',
        '### Implementation and release gates', '',
        '- [x] Add government-host catalog, normalized excerpt hashes and per-passage provenance.',
        '- [x] Implement read-only FTS preview, public API and `/sec-core` frontend.',
        '- [x] Implement explicit bounded HTTP intake, conservative parsers and raw/snapshot storage.',
        '- [x] Reparse and hash-check acquired snapshots before idempotent database staging.',
        '- [x] Keep rights/technical approval separate; preserve exact locators in Agent retrieval.',
        '- [x] Add privileged revision-bound applicability review; never use import date as effective date.',
        '- [x] Create GitHub issues #1, #2, #3 with acceptance criteria and dependencies.',
        '- [ ] Complete native publication of the earlier full application; addon publication alone is insufficient.',
        '- [ ] Acquire and validate complete Core source publications; live network intake blocked in this environment.',
        '- [ ] Review HTML selectors, PDF/table layouts and citation completeness against actual full sources.',
        '- [ ] Exercise the shared PostgreSQL rate budget and controlled egress on deployed infrastructure.',
        '- [ ] Perform real independent rights, technical and historical-applicability reviews.',
        '- [ ] Replace legacy 2,000-source Agent retrieval bound; validate persistent retrieval at corpus scale.',
        '- [ ] Create professionally adjudicated accounting/citation benchmarks and source-update monitoring.', '',
        'Observed local checks: 248 Python tests passed (203 baseline + 45 new); TypeScript typecheck and demo build passed. Mocked acquisition/reviewer fixtures are not live downloads or real professional approvals. No live Gemini, Identity Platform, PostgreSQL or cloud deployment was performed.', '',
        'Commands: `PYTHONPATH=backend python -m app.sec_core validate`; `python scripts/sec_core_progress.py --write`; `python scripts/sec_core_progress.py --check`. Full details: `docs/sec/README.md`.', '', END]
    return '\n'.join(lines), report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--write',action='store_true');g.add_argument('--check',action='store_true')
    args=p.parse_args();section,report=render()
    progress=ROOT/'progress.md'
    text=progress.read_text() if progress.exists() else '# Open Source Accounting — progress\n'
    if START in text and END in text:
        existing=text[text.index(START):text.index(END)+len(END)]
        expected=text.replace(existing,section)
    else:
        expected=text.rstrip()+'\n\n'+section+'\n'
    report_path=ROOT/'content/sec_core/coverage.json'
    md_path=ROOT/'docs/sec/progress.md'
    outputs={progress:expected,report_path:json.dumps(report,indent=2)+'\n',md_path:section+'\n'}
    if args.check:
        for path,wanted in outputs.items():
            if not path.exists() or path.read_text()!=wanted:
                raise SystemExit(f'Stale SEC progress file: {path.relative_to(ROOT)}; run --write')
        print('SEC coverage and queue tracking are current.')
    else:
        for path,wanted in outputs.items():
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(wanted)
        print('Updated progress.md, SEC progress and coverage JSON.')
if __name__=='__main__':main()
