"""Exact-government-source pilot integrity and fail-closed public boundary tests."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PREFIX='content/irs-source-pilot/2026-10-04/'
CHECKER=ROOT/'scripts/check_public.py'

def policy_namespace():
    tree=ast.parse(CHECKER.read_text())
    names={'EXACT','TAX_CASE_FILES','CORE_STANDARDS_FILES','SALT_FILES','IRS_SOURCE_FILES'}
    nodes=[n for n in tree.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name=='allowed')]
    scope={'Path':Path}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(CHECKER),'exec'),scope)
    return scope

class IRSSourcePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=policy_namespace()
        cls.manifest=json.loads((ROOT/PREFIX/'manifest.json').read_text())
    def test_exact_eighteen_original_and_thirty_six_total_paths(self):
        self.assertEqual(18, sum(name.startswith(PREFIX) for name in self.policy['IRS_SOURCE_FILES']))
        self.assertEqual(36, len(self.policy['IRS_SOURCE_FILES']))
        for name in self.policy['IRS_SOURCE_FILES']:
            self.assertTrue(self.policy['allowed'](name))
    def test_second_batch_eight_complete_documents(self):
        prefix='content/irs-source-pilot/2026-10-04-batch-02/'
        self.assertEqual(18,sum(name.startswith(prefix) for name in self.policy['IRS_SOURCE_FILES']))
        manifest=json.loads((ROOT/prefix/'manifest.json').read_text())
        self.assertEqual(8,len(manifest['documents']))
        self.assertEqual(6,sum(d['document_type']=='notice' for d in manifest['documents']))
        self.assertEqual(2,sum(d['document_type']=='revenue_procedure' for d in manifest['documents']))
        for d in manifest['documents']:
            for key in ['original_pdf','full_text']:
                data=(ROOT/prefix/d[key]['path']).read_bytes()
                self.assertEqual(d[key]['bytes'],len(data))
                self.assertEqual(d[key]['sha256'],hashlib.sha256(data).hexdigest())
            self.assertFalse(d['rights']['government_text_relicensed'])
            self.assertFalse(d['rights']['first_party_noncommercial_terms_apply_to_government_text'])
            self.assertEqual('Ray Sang’s Annotation',d['annotation']['label'])
            for key in ['current_law_claim','current_applicability_reviewed','professionally_reviewed','agent_admitted','original_authored_article']:
                self.assertFalse(d[key])
    def test_second_batch_unknown_and_tampered_source_rejected(self):
        prefix='content/irs-source-pilot/2026-10-04-batch-02/'
        with tempfile.TemporaryDirectory() as directory:
            r=Path(directory);(r/'scripts').mkdir();(r/'scripts/check_public.py').write_bytes(CHECKER.read_bytes())
            subprocess.run(['git','init','-q',str(r)],check=True)
            p=r/prefix/'originals/n-25-22.pdf';p.parent.mkdir(parents=True);p.write_bytes(b'%PDF-1.7 tampered')
            result=subprocess.run(['python',str(r/'scripts/check_public.py')],capture_output=True,text=True)
            self.assertNotEqual(0,result.returncode)
            self.assertIn('IRS source hash mismatch',result.stderr)
            p.rename(p.with_name('unapproved.pdf'))
            result=subprocess.run(['python',str(r/'scripts/check_public.py')],capture_output=True,text=True)
            self.assertNotEqual(0,result.returncode)
            self.assertIn('unapproved.pdf',result.stderr)
    def test_second_batch_sibling_unknown_files_denied(self):
        for name in ['unapproved.md','unapproved.json','originals/unapproved.pdf','text/unapproved.txt','premium_private/manifest.json']:
            self.assertFalse(self.policy['allowed']('content/irs-source-pilot/2026-10-04-batch-02/'+name))
    def test_unknown_pdf_and_text_denied(self):
        for name in ['originals/unreviewed.pdf','text/unreviewed.txt','unreviewed.md','manifest.json.extra','later/manifest.json']:
            self.assertFalse(self.policy['allowed'](PREFIX+name))
    def test_another_edition_not_implicitly_allowed(self):
        self.assertFalse(self.policy['allowed']('content/irs-source-pilot/2026-10-05/manifest.json'))
    def test_private_payload_paths_denied(self):
        self.assertFalse(self.policy['allowed'](PREFIX+'premium_private/manifest.json'))
    def test_exact_approved_file_hashes(self):
        for name,expected in self.policy['IRS_SOURCE_FILES'].items():
            p=ROOT/name
            self.assertFalse(p.is_symlink())
            self.assertEqual(expected,hashlib.sha256(p.read_bytes()).hexdigest())
    def test_eight_originals_and_complete_texts(self):
        self.assertEqual(8,len(self.manifest['documents']))
        for d in self.manifest['documents']:
            for key in ['original_pdf','full_text']:
                data=(ROOT/PREFIX/d[key]['path']).read_bytes()
                self.assertEqual(d[key]['bytes'],len(data))
                self.assertEqual(d[key]['sha256'],hashlib.sha256(data).hexdigest())
            self.assertTrue((ROOT/PREFIX/d['original_pdf']['path']).read_bytes().startswith(b'%PDF-'))
    def test_no_currency_professional_or_agent_claims(self):
        for d in self.manifest['documents']:
            self.assertFalse(d['current_law_claim'])
            self.assertFalse(d['current_applicability_reviewed'])
            self.assertFalse(d['professionally_reviewed'])
            self.assertFalse(d['agent_admitted'])
            self.assertFalse(d['original_authored_article'])
    def test_government_text_not_relicensed(self):
        for d in self.manifest['documents']:
            self.assertFalse(d['rights']['government_text_relicensed'])
            self.assertFalse(d['rights']['first_party_noncommercial_terms_apply_to_government_text'])
            self.assertEqual('Ray Sang’s Annotation',d['annotation']['label'])
            self.assertTrue(d['source_url'].startswith('https://www.irs.gov/pub/irs-drop/'))
    def test_advance_copy_limitation_preserved(self):
        d=next(d for d in self.manifest['documents'] if d['official_identifier']=='Revenue Ruling 2026-20')
        self.assertIsNone(d['irb_publication_date'])
        self.assertIn('advance copy',d['edition_status'])
    def test_unknown_and_tampered_source_rejected_by_real_checker(self):
        with tempfile.TemporaryDirectory() as directory:
            r=Path(directory);(r/'scripts').mkdir();(r/'scripts/check_public.py').write_bytes(CHECKER.read_bytes())
            subprocess.run(['git','init','-q',str(r)],check=True)
            p=r/PREFIX/'text/rr-19-24.txt';p.parent.mkdir(parents=True);p.write_text('tampered source')
            result=subprocess.run(['python',str(r/'scripts/check_public.py')],capture_output=True,text=True)
            self.assertNotEqual(0,result.returncode)
            self.assertIn('IRS source hash mismatch',result.stderr)
            p.rename(p.with_name('unapproved.txt'))
            result=subprocess.run(['python',str(r/'scripts/check_public.py')],capture_output=True,text=True)
            self.assertNotEqual(0,result.returncode)
            self.assertIn('unapproved.txt',result.stderr)

if __name__=='__main__':unittest.main()
