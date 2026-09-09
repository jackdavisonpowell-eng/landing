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

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

NO_CACHE = (".html", ".json", ".md", ".txt", "/")
BRIEF = 300          # seconds; media
DEFAULT = 3600       # seconds; css, fonts, anything else


class Handler(SimpleHTTPRequestHandler):
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
