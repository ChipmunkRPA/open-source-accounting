#!/usr/bin/env python3
"""Generate a reproducible content inventory inside progress.md; --check detects stale tracking."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
START='<!-- CONTENT-INVENTORY:START -->';END='<!-- CONTENT-INVENTORY:END -->'

def render(root=ROOT):
    m=json.loads((root/'content/manifest.json').read_text());q=json.loads((root/'content/qa/questions.json').read_text())
    rows=defaultdict(Counter);lookup={i['id']:i for i in m['items']}
    for i in m['items']:
        rows[i['topic']][i['kind']]+=1
        rows[i['topic']]['reviewed']+=i['technical_review']['status']=='reviewed'
    for x in q['questions']:rows[lookup[x['related_item_id']]['topic']]['questions']+=1
    lines=[START,'',f"Manifest release **{m['release']}**: **{len(m['items'])} items**, **{len(q['questions'])} study questions**. Counts are coverage indicators, not quality scores.",'',
        '| Topic | Guides | Cases | Templates | Playbooks | Q&A sets | Questions | Human-reviewed items | Next gate |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for topic,c in sorted(rows.items()):
        lines.append('| '+topic+' | '+' | '.join(str(c[k]) for k in ['guide','case','template','playbook','qa_set','questions','reviewed'])+' | '+('Independent technical review; then authority/access validation' if not c['reviewed'] else 'Version maintenance and benchmark review')+' |')
    lines+=['','All draft items remain ineligible for automatic Agent admission. Rights approval and technical review are separate, revision-bound gates.',END]
    return '\n'.join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    path=ROOT/'progress.md';text=path.read_text();section=render()
    if START not in text or END not in text:raise SystemExit('Missing inventory markers.')
    old=text[text.index(START):text.index(END)+len(END)]
    if a.check:
        if old!=section:raise SystemExit('Content inventory is stale: run python scripts/content_progress.py')
        print('Content inventory matches manifest and questions.');return
    path.write_text(text.replace(old,section));print('Updated progress.md content inventory.')
if __name__=='__main__':main()
