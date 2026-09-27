#!/usr/bin/env python3
"""Validate the original library, Q&A cross-references and illustrative arithmetic."""
import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.content import Library

def check():
    lib=Library(ROOT/'content')
    qa=json.loads((ROOT/'content/qa/questions.json').read_text())['questions']
    seen=set()
    for q in qa:
        assert q['id'] not in seen, 'Duplicate Q&A ID'
        seen.add(q['id'])
        assert q['related_item_id'] in lib.items
        assert set(q['source_ids']).issubset(lib.references)
        assert q['license']=='CC-BY-4.0'
        assert q['review_status']=='unreviewed', 'A review cannot be inferred from a test pass.'
    with localcontext() as c:
        c.prec=36
        p=Decimal('10000');r=Decimal('.06')
        pv=sum(p/(1+r)**t for t in range(1,4))
        assert pv.quantize(Decimal('.01'))==Decimal('26730.12')
        b=pv
        for _ in range(3):b=b*(1+r)-p
        assert abs(b)<Decimal('1e-20')
        assert Decimal('90000')*Decimal('.8')==Decimal('72000')
    result={**lib.report(),'qa_records':len(qa),'arithmetic_examples_checked':3,
            'technical_accounting_review_performed':False,'external_link_check_performed':False}
    print(json.dumps(result,indent=2))
    return result
if __name__=='__main__':check()
