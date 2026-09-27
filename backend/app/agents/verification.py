from ..schemas import Analysis


def structural_verify(analysis: Analysis, evidence):
    """Checks provenance structure, not semantic truth. Semantic review is a separate pass."""
    findings = []
    evidence_map = {x['id']: x for x in evidence}
    ids = [x.id for x in analysis.claims]
    if len(set(ids)) != len(ids):
        findings.append({'claim_id': 'GLOBAL', 'severity': 'block', 'reason': 'Duplicate claim identifiers.'})
    for claim in analysis.claims:
        if any(eid not in evidence_map for eid in claim.evidence_ids):
            findings.append({'claim_id': claim.id, 'severity': 'block', 'reason': 'Unknown evidence ID.'})
        usable = [evidence_map[eid] for eid in claim.evidence_ids if eid in evidence_map and
                  evidence_map[eid]['access'] != 'reference_only']
        if claim.basis == 'source' and not usable:
            findings.append({'claim_id': claim.id, 'severity': 'block', 'reason': 'Source claim lacks reviewed evidence.'})
    for section in analysis.sections:
        if any(cid not in ids for cid in section.claim_ids):
            findings.append({'claim_id': 'GLOBAL', 'severity': 'block', 'reason': 'Section contains an unknown claim ID.'})
    for table in analysis.tables:
        if any(eid not in evidence_map for eid in table.evidence_ids):
            findings.append({'claim_id': 'GLOBAL', 'severity': 'block', 'reason': 'Table contains an unknown evidence ID.'})
    return findings
