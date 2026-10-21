from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
root=Path(__file__).resolve().parents[2]
print("http://127.0.0.1:8771/tutorials/full-doll-o22/index.html",flush=True)
ThreadingHTTPServer(("127.0.0.1",8771),partial(SimpleHTTPRequestHandler,directory=str(root))).serve_forever()
