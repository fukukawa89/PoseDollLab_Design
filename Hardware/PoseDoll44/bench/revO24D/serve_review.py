"""Local-only review server. Standard Python 3; no third-party dependencies."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

root=Path(__file__).resolve().parent
for port in range(8788,8800):
    try:
        server=ThreadingHTTPServer(('127.0.0.1',port),partial(SimpleHTTPRequestHandler,directory=str(root)))
        break
    except OSError:
        continue
else:
    raise SystemExit('Ports 8788-8799 are in use; close a previous review server and retry.')
url=f'http://127.0.0.1:{port}/REVIEW.html'
print(url,flush=True)
webbrowser.open(url)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
