"""Local preview; exposes only built public assets, never the repository."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
ROOT=Path(__file__).resolve().parents[1]/'frontend/dist'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        path=unquote(urlsplit(self.path).path)
        if path.startswith('/api/'):
            self.send_response(503); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(b'{"error":{"code":"API_UNAVAILABLE","message":"Hosted API is not configured in the local public preview"}}'); return
        if path.startswith('/assets/'):
            path=path[len('/assets/'):]
        else:
            path='index.html'
        target=(ROOT/path).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            self.send_error(404); return
        self.path='/'+target.relative_to(ROOT.resolve()).as_posix()
        super().do_GET()
    def do_HEAD(self):
        self.send_error(405)
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8080)
    args=parser.parse_args()
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
