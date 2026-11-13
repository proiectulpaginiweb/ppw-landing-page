#!/usr/bin/env python3
"""Serve the static site locally with explicit UTF-8 for text responses."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class UTF8Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.md': 'text/markdown'}

    def guess_type(self, path):
        content_type = super().guess_type(path)
        if content_type.startswith('text/') or content_type in {
            'application/javascript', 'application/json', 'application/xml', 'image/svg+xml'
        }:
            return content_type + '; charset=utf-8'
        return content_type


if __name__ == '__main__':
    handler = partial(UTF8Handler, directory=str(ROOT))
    with ThreadingHTTPServer(('127.0.0.1', 4173), handler) as server:
        print('Serving PPW at http://127.0.0.1:4173 (UTF-8)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
