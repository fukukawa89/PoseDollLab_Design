from pathlib import Path
import http.server,functools,threading,webbrowser
root=Path(__file__).resolve().parent
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root.parent)))
url=f'http://127.0.0.1:{server.server_address[1]}/{root.name}/index.html'
print(url);threading.Timer(.3,lambda:webbrowser.open(url)).start()
try:server.serve_forever()
except KeyboardInterrupt:server.server_close()
