from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import os,webbrowser
os.chdir(Path(__file__).parent)
webbrowser.open("http://127.0.0.1:8765/")
ThreadingHTTPServer(("127.0.0.1",8765),SimpleHTTPRequestHandler).serve_forever()
