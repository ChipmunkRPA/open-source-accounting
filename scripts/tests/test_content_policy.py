"""Regression checks for private-only fixture export and advisory root routes."""
import ast
from pathlib import Path
import unittest
import importlib.util
import http.client
import threading
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def guard_functions():
    source = ast.parse((ROOT / 'scripts/check_public.py').read_text())
    selected = [node for node in source.body if isinstance(node, ast.FunctionDef)
                and node.name in {'contains_private_fiction', 'fiction_file_error'}]
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), 'public-boundary', 'exec'), namespace)
    return namespace


class BoundaryTests(unittest.TestCase):
    def test_private_marker_rejected_at_every_depth(self):
        check = guard_functions()['contains_private_fiction']
        for row in [
            {'content_purpose': 'fictional_copyright_detection'},
            {'storage_scope': 'premium_private'},
            {'id': 'osa-fiction-detection-boundary-test'},
        ]:
            for value in [row, [row], {'items': [{'metadata': row}]}]:
                with self.subTest(value=value):
                    self.assertTrue(check(value))

    def test_missing_review_is_not_fiction(self):
        check = guard_functions()['contains_private_fiction']
        for row in [{}, {'professional_review': False}, {'technical_review': {'status': 'unreviewed'}},
                    {'content_purpose': 'original_annotation'}, {'publisher': 'Government'}]:
            self.assertFalse(check(row))

    def test_policy_metadata_is_not_a_private_item(self):
        import json
        self.assertFalse(guard_functions()['contains_private_fiction'](
            json.loads((ROOT / 'content/annotation-policy.json').read_text())))

    def test_json_and_markdown_boundary_fails_closed(self):
        import tempfile
        check = guard_functions()['fiction_file_error']
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'probe.json'
            p.write_text('{broken')
            self.assertTrue(check(p))
            p.write_text('{"content_purpose":"fictional_copyright_detection","content_purpose":"original_annotation"}')
            self.assertTrue(check(p))
            p.write_text('{"nested":[{"storage_scope":"premium_private"}]}')
            self.assertTrue(check(p))
            p.write_text('{"professional_review":false}')
            self.assertFalse(check(p))
            p = Path(temp) / 'probe.md'
            p.write_text('osa-fiction-detection-boundary-test')
            self.assertTrue(check(p))

    def test_actual_export_command_rejects_private_marker(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', dir=ROOT / 'content') as probe:
            probe.write('{"content_purpose":"fictional_copyright_detection"}')
            probe.flush()
            result = subprocess.run([sys.executable, 'scripts/check_public.py'], cwd=ROOT,
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('(private fiction)', result.stderr + result.stdout)


class RootRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('policy_public_server', ROOT / 'scripts/serve_public.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.server = module.ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def get(self, path):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_address[1])
        try:
            connection.request('GET', path)
            response = connection.getresponse()
            return response.status, response.getheader('Content-Type'), response.read().decode()
        finally:
            connection.close()

    def test_root_robots_is_text_not_spa_fallback(self):
        status, mime, body = self.get('/robots.txt')
        self.assertEqual(status, 200)
        self.assertTrue(mime.startswith('text/plain'))
        self.assertEqual(body, (ROOT / 'robots.txt').read_text())

    def test_root_terms_are_current_exact_terms(self):
        status, mime, body = self.get('/content-terms.txt')
        self.assertEqual(status, 200)
        self.assertTrue(mime.startswith('text/plain'))
        self.assertEqual(body, (ROOT / 'CONTENT-TERMS.md').read_text())

    def test_original_pages_branded_and_repository_traversal_refused(self):
        for path in ['/assets/library/index.html', '/assets/library/authority-and-period.html',
                     '/assets/systems/index.html', '/assets/systems/xero.html']:
            status, _, body = self.get(path)
            self.assertEqual(status, 200)
            self.assertIn('Ray Sang’s Annotation', body)
        self.assertEqual(self.get('/assets/../../CONTENT-TERMS.md')[0], 404)


if __name__ == '__main__':
    unittest.main()
