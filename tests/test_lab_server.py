import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from retail_media.lab_server import create_server
from retail_media.lab_model import SERVING_ID


class FakeSimulation:
    def __init__(self, **options):
        self.options = options
        self.steps = 0
        self.done = False

    def snapshot(self):
        return {'progress': self.steps / 10, 'done': self.done,
                'metrics': {'sessions_completed': 0}, 'current': {'products': []}}

    def advance(self, steps=1):
        self.steps += steps
        self.done = self.steps >= 10
        return self.snapshot()


class LabServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.public = self.root / 'public'
        self.public.mkdir()
        (self.public / 'index.html').write_text('<h1>Lab</h1>')
        (self.root / 'private.txt').write_text('PRIVATE')
        self.server = create_server(port=0, public_dir=self.public,
                                    workspace=self.root, simulation_factory=FakeSimulation)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.assertFalse(self.thread.is_alive())
        self.directory.cleanup()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        data = json.dumps(body).encode() if body is not None else None
        request_headers = {'Content-Type': 'application/json', **(headers or {})}
        conn.request(method, path, body=data, headers=request_headers)
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result

    def test_real_session_controls_and_close(self):
        status, _, raw = self.request('POST', '/api/simulations', {'seed': 1})
        self.assertEqual(status, 201)
        session_id = json.loads(raw)['id']
        status, _, raw = self.request('POST', f'/api/simulations/{session_id}/advance', {'steps': 8})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['progress'], .8)
        self.assertEqual(self.request('DELETE', f'/api/simulations/{session_id}')[0], 204)
        self.assertEqual(self.request('GET', f'/api/simulations/{session_id}')[0], 404)

    def test_parameters_validated_and_batch_bounded(self):
        for body in ({'sessions': 0}, {'sessions': 50001}, {'seed': -1}, {'seed': True},
                     {'policy': 'unknown'}, {'scenario': 'typo'}, {'budget_scale': 0},
                     {'budget_scale': float('nan')}, {'unexpected': 1}):
            with self.subTest(body=body):
                self.assertEqual(self.request('POST', '/api/simulations', body)[0], 400)
        _, _, raw = self.request('POST', '/api/simulations', {})
        session_id = json.loads(raw)['id']
        self.assertEqual(self.request('POST', f'/api/simulations/{session_id}/advance', {'steps': 201})[0], 400)

    def test_cross_origin_mutation_rejected_and_security_headers(self):
        status, headers, _ = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn("default-src 'self'", headers['Content-Security-Policy'])
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(self.request('POST', '/api/simulations', {}, {'Origin': 'https://evil.example'})[0], 403)

    def test_traversal_and_private_workspace_files_not_served(self):
        for path in ['/../private.txt', '/%2e%2e/private.txt', '/.git/config', '/artifacts/model.npz']:
            with self.subTest(path=path):
                status, _, raw = self.request('GET', path)
                self.assertIn(status, [403, 404])
                self.assertNotIn(b'PRIVATE', raw)

    def test_missing_report_has_explicit_state_and_pool_is_bounded(self):
        status, _, raw = self.request('GET', '/api/evaluation')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['status'], 'not_available')
        for _ in range(12):
            self.assertEqual(self.request('POST', '/api/simulations', {})[0], 201)
        self.assertEqual(self.request('POST', '/api/simulations', {})[0], 429)

    def test_evaluation_must_match_the_active_learned_parameters(self):
        reports = self.root / 'reports'
        reports.mkdir()
        path = reports / 'lab_evaluation.json'
        path.write_text(json.dumps({'model_id': 'previous', 'scenarios': {}}))
        self.server.model_identity_provider = lambda: 'active'
        status, _, raw = self.request('GET', '/api/evaluation')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['status'], 'stale')
        path.write_text(json.dumps({'model_id': 'active', 'serving_id': SERVING_ID, 'scenarios': {}}))
        _, _, raw = self.request('GET', '/api/evaluation')
        self.assertEqual(json.loads(raw)['status'], 'ready')

    def test_competition_report_missing_stale_and_ready(self):
        self.assertEqual(json.loads(self.request('GET', '/api/competition')[2])['status'], 'not_available')
        reports = self.root / 'reports'
        reports.mkdir()
        path = reports / 'lab_competition.json'
        self.server.model_identity_provider = lambda: 'active'
        path.write_text(json.dumps({'model_id': 'old'}))
        self.assertEqual(json.loads(self.request('GET', '/api/competition')[2])['status'], 'stale')
        path.write_text(json.dumps({'schema': 'retail_lab_competition_v1', 'model_id': 'active'}))
        self.assertEqual(json.loads(self.request('GET', '/api/competition')[2])['status'], 'stale')
        path.write_text(json.dumps({'schema': 'retail_lab_competition_v3_plp16', 'model_id': 'active', 'serving_id': SERVING_ID, 'scenarios': {}}))
        result = json.loads(self.request('GET', '/api/competition')[2])
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['report']['model_id'], 'active')


if __name__ == '__main__':
    unittest.main()
