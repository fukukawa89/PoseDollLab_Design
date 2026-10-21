from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import os,webbrowser
os.chdir(Path(__file__).parent)
webbrowser.open("http://127.0.0.1:8764/")
ThreadingHTTPServer(("127.0.0.1",8764),SimpleHTTPRequestHandler).serve_forever()
