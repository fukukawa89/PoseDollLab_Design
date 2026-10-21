"""Standalone preview launcher, copied into the O22F7 print package."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import uuid
import webbrowser

VERSION = "O22F7"


class PreviewServer(ThreadingHTTPServer):
    # On Windows, SO_REUSEADDR can bind to a running older preview server.
    allow_reuse_address = False
    allow_reuse_port = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory, prefix, **kwargs):
        self.preview_prefix = prefix
        super().__init__(*args, directory=directory, **kwargs)

    def send_head(self):
        if not self.path.startswith(self.preview_prefix):
            self.send_error(404, "Open the URL shown by this O22F7 launcher.")
            return None
        # Always serve this package, including when the browser revalidates a tab.
        if "If-Modified-Since" in self.headers:
            del self.headers["If-Modified-Since"]
        return super().send_head()

    def translate_path(self, path):
        return super().translate_path("/" + path[len(self.preview_prefix):])

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-PoseDoll-Version", VERSION)
        super().end_headers()


def create_preview(root):
    root = Path(root).resolve()
    if not (root / "index.html").is_file():
        raise FileNotFoundError("Extract the complete O22F7 package before opening it.")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8-sig"))
    if manifest.get("version") != "O22F7-PLA-Final":
        raise ValueError("This launcher belongs beside the O22F7 package's index.html.")
    # Port 0 requests an unused port. The unique path also isolates all relative
    # JS/model URLs from browser caches of earlier preview sessions.
    prefix = f"/{VERSION}-{uuid.uuid4().hex}/"
    handler = partial(PreviewHandler, directory=str(root), prefix=prefix)
    server = PreviewServer(("127.0.0.1", 0), handler)
    url = f"http://127.0.0.1:{server.server_port}{prefix}index.html"
    return server, url


def main():
    parser = argparse.ArgumentParser(description="Open the O22F7 local 3D preview.")
    parser.add_argument("--no-browser", action="store_true", help="Print the URL without opening a tab.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    server, url = create_preview(root)
    with server:
        print(f"{VERSION} PLA preview", flush=True)
        print(f"Package: {root}", flush=True)
        print(f"Preview URL: {url}", flush=True)
        print("Keep this window open while viewing. Press Ctrl+C to stop.", flush=True)
        if not args.no_browser and not webbrowser.open(url):
            print("Open the Preview URL above in your browser.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
