"""Serve local PoseDoll docs with explicit UTF-8 and retired-entry redirects."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,unquote
import argparse
ROOT=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44'
REDIRECTS={
 '/tutorials/full-doll/':'/tutorials/full-doll-o14/index.html',
 '/tutorials/full-doll/index.html':'/tutorials/full-doll-o14/index.html',
 '/bench/revO13/README.zh-CN.md':'/tutorials/core-print/index.html',
 '/bench/revO13/print_beds/O13_core_fit_only.3mf':'/tutorials/core-print/index.html#download',
}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def guess_type(self,path):
  kind=super().guess_type(path)
  if str(path).lower().endswith('.md'):kind='text/plain'
  if kind.startswith('text/') or kind in ('application/json','application/javascript'):kind+='; charset=utf-8'
  return kind
 def send_head(self):
  target=REDIRECTS.get(unquote(urlsplit(self.path).path))
  if target:
   self.send_response(302);self.send_header('Location',target);self.send_header('Content-Length','0');self.end_headers();return None
  return super().send_head()
 def end_headers(self):
  self.send_header('Cache-Control','no-cache');super().end_headers()
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8769);args=ap.parse_args()
 print('PoseDoll UTF-8 tutorials: http://127.0.0.1:%d/tutorials/full-doll-o14/index.html'%args.port,flush=True)
 ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
