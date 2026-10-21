from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import webbrowser
root=Path(__file__).resolve().parent
with ThreadingHTTPServer(('127.0.0.1',8772),partial(SimpleHTTPRequestHandler,directory=str(root))) as server:
    url='http://127.0.0.1:8772/tutorials/assembly-o22/index.html'
    print(url+'  (Ctrl+C to stop)')
    webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
