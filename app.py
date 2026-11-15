import argparse
import json
import os
from pathlib import Path
import secrets
import socket
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import DEFAULT
TOKEN = secrets.token_urlsafe(32)
ORIGIN = ''
DEMO = False

def broker(req):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(20)
        try:
            s.connect('/var/run/bootpd-panel.sock')
        except OSError as e:
            raise ValueError('Helper unavailable. Start or reinstall the helper.') from e
        s.sendall(json.dumps(req).encode() + b'\n')
        with s.makefile('rb') as f:
            response = json.loads(f.readline(4 * 1024 * 1024))
    if not response['ok']:
        raise ValueError(response['error'])
    return response['result']

class Handler(BaseHTTPRequestHandler):
    timeout = 10

    def log_message(self, *_):
        pass

    def reply(self, code, body, content='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', content)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get('Host') != ORIGIN.removeprefix('http://'):
            return self.reply(403, {'error': 'Host not allowed'})
        path = self.path.split('?', 1)[0]
        files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if path not in files:
            return self.reply(404, {})
        (name, mime) = files[path]
        self.reply(200, (Path(__file__).parent / 'static' / name).read_bytes(), mime)

    def do_POST(self):
        if self.headers.get('Host') != ORIGIN.removeprefix('http://') or self.headers.get('Origin') != ORIGIN or (not secrets.compare_digest(self.headers.get('X-Session', ''), TOKEN)):
            return self.reply(403, {'error': 'Invalid origin or session token'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384 or self.path != '/api':
                raise ValueError('Invalid request')
            req = json.loads(self.rfile.read(size))
            if not isinstance(req, dict):
                raise ValueError('Invalid request')
            if DEMO:
                if req.get('op') != 'status':
                    raise ValueError('Demo mode: controls are disabled')
                result = dict(running=False, config=DEFAULT, interfaces=[], leases=[], history=[], backups=[], demo=True)
            else:
                result = broker(req)
            self.reply(200, result)
        except Exception as e:
            self.reply(400, {'error': str(e)})

def main():
    global ORIGIN, DEMO
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8765)
    p.add_argument('--demo', action='store_true')
    a = p.parse_args()
    if os.geteuid() == 0:
        raise SystemExit('Run the web interface as a regular user')
    DEMO = a.demo
    server = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    ORIGIN = 'http://127.0.0.1:' + str(server.server_port)
    server.timeout = 10
    print('Open: ' + ORIGIN + '/#' + TOKEN, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
if __name__ == '__main__':
    main()
