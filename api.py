import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from uuid import UUID
from domain import connect, create_order, finish_repair

ROLE = os.getenv('ROLE', 'orders')
DB = os.getenv('DB', '/data/service.db')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.dispatch('GET')

    def do_POST(self):
        self.dispatch('POST')

    def dispatch(self, method):
        db = connect(DB)
        code, result = 200, None
        try:
            path = urlsplit(self.path)
            parts = path.path.strip('/').split('/')
            if method == 'GET' and parts == ['health']:
                result = {'status': 'ok', 'service': ROLE}
            elif parts[:2] != ['api', ROLE]:
                raise KeyError('route')
            elif method == 'GET' and len(parts) == 2:
                q = parse_qs(path.query)
                limit = int(q.get('limit', ['20'])[0])
                offset = int(q.get('offset', ['0'])[0])
                if not 1 <= limit <= 100 or offset < 0:
                    raise ValueError('pagination')
                result = [dict(r) for r in db.execute(
                    f'SELECT * FROM {ROLE} ORDER BY rowid LIMIT ? OFFSET ?',
                    (limit, offset))]
            elif method == 'GET' and len(parts) == 3:
                UUID(parts[2])
                r = db.execute(f'SELECT * FROM {ROLE} WHERE id=?',
                               (parts[2],)).fetchone()
                if r is None:
                    raise KeyError('not_found')
                result = dict(r)
            elif method == 'POST' and ROLE == 'orders' and len(parts) == 2:
                size = int(self.headers.get('Content-Length', '0'))
                if not 1 <= size <= 16384:
                    raise ValueError('body_size')
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError('object_required')
                result, code = create_order(db, data), 201
            elif (method == 'POST' and ROLE == 'repairs' and
                  len(parts) == 4 and parts[3] == 'complete'):
                UUID(parts[2])
                result = finish_repair(db, parts[2])
            else:
                raise KeyError('route')
        except (ValueError, TypeError) as e:
            code, result = 400, {'error': str(e)}
        except KeyError:
            code, result = 404, {'error': 'not_found'}
        except RuntimeError as e:
            code, result = 409, {'error': str(e)}
        except Exception:
            code, result = 500, {'error': 'internal_error'}
        finally:
            db.close()
        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
