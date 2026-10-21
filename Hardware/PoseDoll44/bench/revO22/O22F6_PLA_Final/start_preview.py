from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import os,webbrowser
os.chdir(Path(__file__).parent)
for port in range(8766,8777):
 try:
  server=ThreadingHTTPServer(("127.0.0.1",port),SimpleHTTPRequestHandler)
  break
 except OSError:pass
else:raise RuntimeError("No free local preview port")
webbrowser.open(f"http://127.0.0.1:{port}/")
server.serve_forever()
