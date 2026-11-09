"""HTTP local para el laboratorio: sesiones aisladas e inferencia real en Python."""
import json
import math
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import unquote, urlsplit

from .lab_model import SERVING_ID


ROOT = Path(__file__).resolve().parent.parent
PUBLIC = Path(__file__).with_name('web')
POLICIES = ['safe_rl', 'greedy', 'quality', 'relevance', 'bid', 'random', 'organic']
SCENARIOS = ['balanced', 'clickbait', 'scarce', 'shift']


def _reject_constant(value):
    raise ValueError(f'Número no válido: {value}')


class SimulationStore:
    def __init__(self, factory, limit=12, ttl=3600):
        self.factory, self.limit, self.ttl = factory, limit, ttl
        self.entries = {}
        self.lock = threading.RLock()

    def create(self, options):
        with self.lock:
            now = time.monotonic()
            self.entries = {key: value for key, value in self.entries.items() if now - value['touched'] < self.ttl}
            if len(self.entries) >= self.limit:
                raise OverflowError('Hay demasiadas simulaciones abiertas. Reinicia o cierra una.')
            simulation = self.factory(**options)
            key = secrets.token_urlsafe(18)
            self.entries[key] = {'simulation': simulation, 'touched': now, 'lock': threading.Lock()}
            return key, simulation.snapshot()

    def get(self, key):
        with self.lock:
            entry = self.entries.get(key)
            if not entry or time.monotonic() - entry['touched'] >= self.ttl:
                self.entries.pop(key, None)
                raise KeyError('La simulación terminó o expiró. Inicia una nueva.')
            entry['touched'] = time.monotonic()
            return entry


def create_server(port=8765, public_dir=PUBLIC, workspace=ROOT, simulation_factory=None):
    workspace, public_dir = Path(workspace).resolve(), Path(public_dir).resolve()
    identity_provider = lambda: None
    if simulation_factory is None:
        from .lab_engine import LabSimulation
        from .lab_model import LabModel
        cached_model, cached_stamp = None, None
        def current_model():
            nonlocal cached_model, cached_stamp
            path = workspace / 'artifacts/lab_model.npz'
            stamp = path.stat().st_mtime_ns
            if cached_model is None or cached_stamp != stamp:
                cached_model, cached_stamp = LabModel.load(path), stamp
            return cached_model
        def simulation_factory(**options):
            # Model parameters are frozen; sessions own their RNG and balances.
            return LabSimulation(model=current_model(), **options)
        identity_provider = lambda: current_model().identity()
    store = SimulationStore(simulation_factory)

    class Handler(BaseHTTPRequestHandler):
        server_version = 'RetailMediaLab/1.0'

        def log_message(self, format, *args):
            # No cookies, payloads or configuration in request logs.
            pass

        def send_common_headers(self, status, kind, size):
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(size))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.send_header('Cache-Control', 'no-store' if self.path.startswith('/api/') else 'no-cache')
            self.end_headers()

        def respond(self, value, status=200):
            data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            self.send_common_headers(status, 'application/json; charset=utf-8', len(data))
            self.wfile.write(data)

        def body(self):
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or length > 32768:
                raise ValueError('La solicitud es demasiado grande')
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('Se requiere application/json')
            data = json.loads(self.rfile.read(length) or b'{}', parse_constant=_reject_constant)
            if not isinstance(data, dict):
                raise ValueError('La solicitud debe ser un objeto JSON')
            return data

        def origin_allowed(self):
            origin = self.headers.get('Origin')
            allowed = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
            return origin is None or origin in allowed

        def route(self, method):
            path = urlsplit(self.path).path
            if method != 'GET' and not self.origin_allowed():
                self.respond({'error': 'Origen de solicitud no permitido'}, 403)
                return
            if method == 'GET' and path == '/api/metadata':
                self.respond({'name': 'Retail Media Lab', 'policies': POLICIES, 'scenarios': SCENARIOS,
                              'model_available': (workspace / 'artifacts/lab_model.npz').exists(),
                              'evaluation_available': (workspace / 'reports/lab_evaluation.json').exists(),
                              'synthetic': True})
                return
            if method == 'GET' and path in ('/api/evaluation', '/api/competition'):
                competition = path == '/api/competition'
                report = workspace / ('reports/lab_competition.json' if competition else 'reports/lab_evaluation.json')
                if not report.exists():
                    self.respond({'status': 'not_available', 'message': 'El informe de impresiones todavía no está disponible. Ejecuta python3 -m retail_media.lab_competition.' if competition else 'La evaluación todavía no está disponible.'})
                    return
                result = json.loads(report.read_text())
                current_id = self.server.model_identity_provider()
                if (not current_id or result.get('model_id') != current_id
                        or result.get('serving_id') != SERVING_ID
                        or (competition and result.get('schema') != 'retail_lab_competition_v3_plp16')):
                    command = 'python3 -m retail_media.lab_competition' if competition else 'python3 -m retail_media evaluate-lab'
                    self.respond({'status': 'stale', 'message': f'Este informe no corresponde al modelo actual. Ejecuta {command} para regenerarlo.'})
                else:
                    self.respond({'status': 'ready', 'report': result})
                return
            if method == 'POST' and path == '/api/simulations':
                data = self.body()
                if set(data) - {'seed', 'policy', 'scenario', 'sessions', 'budget_scale'}:
                    raise ValueError('Hay parámetros desconocidos')
                seed, sessions, scale = data.get('seed', 2026), data.get('sessions', 1000), data.get('budget_scale', 1.)
                if type(seed) is not int or not 0 <= seed < 2 ** 32:
                    raise ValueError('La semilla debe ser un entero entre 0 y 4294967295')
                if type(sessions) is not int or not 10 <= sessions <= 5000:
                    raise ValueError('Elige entre 10 y 5000 sesiones')
                if type(scale) not in (int, float) or not math.isfinite(scale) or not .1 <= scale <= 5:
                    raise ValueError('La inversión debe estar entre 0.1 y 5 veces la base')
                policy, scenario = data.get('policy', 'safe_rl'), data.get('scenario', 'balanced')
                if policy not in POLICIES or scenario not in SCENARIOS:
                    raise ValueError('Política o escenario desconocido')
                key, snapshot = store.create({'seed': seed, 'sessions': sessions, 'budget_scale': scale,
                                              'policy': policy, 'scenario': scenario})
                self.respond({'id': key, **snapshot}, 201)
                return
            parts = path.strip('/').split('/')
            if len(parts) in (3, 4) and parts[:2] == ['api', 'simulations']:
                key = parts[2]
                if method == 'DELETE' and len(parts) == 3:
                    store.get(key)
                    with store.lock:
                        store.entries.pop(key, None)
                    self.send_common_headers(204, 'application/json', 0)
                    return
                entry = store.get(key)
                with entry['lock']:
                    if method == 'GET' and len(parts) == 3:
                        self.respond({'id': key, **entry['simulation'].snapshot()})
                        return
                    if method == 'POST' and parts[3:] == ['advance']:
                        data = self.body()
                        steps = data.get('steps', 1)
                        if set(data) - {'steps'} or type(steps) is not int or not 1 <= steps <= 200:
                            raise ValueError('Cada avance debe tener entre 1 y 200 decisiones')
                        self.respond({'id': key, **entry['simulation'].advance(steps=steps)})
                        return
                self.respond({'error': 'Operación desconocida'}, 404)
                return
            if method != 'GET' or path.startswith('/api/'):
                self.respond({'error': 'Recurso no encontrado'}, 404)
                return
            relative = unquote(path).lstrip('/') or 'index.html'
            file = (public_dir / relative).resolve()
            if not file.is_relative_to(public_dir) or any(part.startswith('.') for part in Path(relative).parts):
                self.respond({'error': 'Recurso no disponible'}, 403)
                return
            if not file.is_file():
                self.respond({'error': 'Recurso no encontrado'}, 404)
                return
            data = file.read_bytes()
            kind = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            if kind.startswith('text/') or file.suffix == '.js':
                kind += '; charset=utf-8'
            self.send_common_headers(200, kind, len(data))
            self.wfile.write(data)

        def handle_route(self, method):
            try:
                self.route(method)
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                self.respond({'error': str(error)}, 400)
            except KeyError:
                self.respond({'error': 'La simulación no existe o expiró. Inicia una nueva.'}, 404)
            except OverflowError as error:
                self.respond({'error': str(error)}, 429)
            except FileNotFoundError:
                self.respond({'error': 'El modelo todavía no está preparado. Ejecuta train-lab primero.'}, 503)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self.respond({'error': 'No se pudo completar la simulación. Reinicia e inténtalo de nuevo.'}, 500)

        def do_GET(self):
            self.handle_route('GET')

        def do_POST(self):
            self.handle_route('POST')

        def do_DELETE(self):
            self.handle_route('DELETE')

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.store = store
    server.model_identity_provider = identity_provider
    return server


def serve(port=8765):
    server = create_server(port=port)
    print(f'Retail Media Lab: http://127.0.0.1:{server.server_port}\nDetener: Ctrl+C', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
