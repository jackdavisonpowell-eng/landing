#!/usr/bin/env python3
"""Static file server for autogod.org, with cache headers that suit editing.

`python3 -m http.server` sends no Cache-Control at all, so Cloudflare falls
back to its own defaults and holds images at the edge for four hours. That is
fine for a site nobody touches and wrong for this one, where the whole point is
that dropping a photo in a folder updates the page. Replacing a file then had
no visible effect until the edge TTL expired.

Pages and data are never cached, so an edit is live immediately. Media is
cached briefly — long enough to help a reader scrolling the page, short enough
that a replaced photo shows up while you are still looking at it.
"""

import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Every /media/ reference in a page gets the file's own modification time
# stamped onto it. Pages are never cached, so replacing a photo changes the
# stamp, which changes the URL, which means the new file is fetched at once —
# no purge, no waiting on an edge TTL, and nothing for the author to remember.
MEDIA = re.compile(
    rb"(/media/[A-Za-z0-9._-]+\.(?:jpg|jpeg|png|webp|gif|avif|mp4|webm|mov|m4v))")

NO_CACHE = (".html", ".json", ".md", ".txt", "/")
BRIEF = 300          # seconds; media
DEFAULT = 3600       # seconds; css, fonts, anything else


class Handler(SimpleHTTPRequestHandler):
    def stamp(self, body):
        def one(m):
            url = m.group(1)
            f = os.path.join(self.directory, url.decode("utf-8").lstrip("/"))
            try:
                return url + b"?v=" + str(int(os.path.getmtime(f))).encode()
            except OSError:
                return url          # not there yet: leave it, the page expects that
        return MEDIA.sub(one, body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path.endswith("/") or path.endswith(".html"):
            f = self.translate_path(path)
            if os.path.isdir(f):
                f = os.path.join(f, "index.html")
            if os.path.isfile(f):
                try:
                    with open(f, "rb") as fh:
                        body = self.stamp(fh.read())
                except OSError:
                    return super().do_GET()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().do_GET()

    def end_headers(self):
        path = self.path.split("?", 1)[0].lower()
        if path.endswith(NO_CACHE):
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        elif path.rsplit(".", 1)[-1] in (
                "jpg", "jpeg", "png", "webp", "gif", "avif",
                "mp4", "webm", "mov", "m4v"):
            self.send_header("Cache-Control", f"public, max-age={BRIEF}")
        else:
            self.send_header("Cache-Control", f"public, max-age={DEFAULT}")
        super().end_headers()

    def log_message(self, *args):
        pass          # the journal does not need a line per asset


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 11480
    root = sys.argv[2] if len(sys.argv) > 2 else "."
    ThreadingHTTPServer(("127.0.0.1", port),
                        partial(Handler, directory=root)).serve_forever()
