#!/usr/bin/env python3
"""Serve the static site locally with explicit UTF-8 for text responses."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://' + (ROOT/'CNAME').read_text(encoding='utf-8').strip() + '/'


class UTF8Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.md': 'text/markdown'}

    def guess_type(self, path):
        content_type = super().guess_type(path)
        if content_type.startswith('text/') or content_type in {
            'application/javascript', 'application/json', 'application/xml', 'image/svg+xml'
        }:
            return content_type + '; charset=utf-8'
        return content_type

    def end_headers(self):
        # Non-HTML copies cannot carry a <link rel="canonical"> in their body.
        request_path = unquote(urlsplit(self.path).path)
        target = (ROOT/request_path.lstrip('/')).resolve()
        if target.is_relative_to(ROOT) and target.suffix == '.md':
            html = target.with_suffix('.html')
            if html.is_file() and html.name == 'index.html':
                directory = html.parent.relative_to(ROOT).as_posix()
                canonical = SITE if directory == '.' else SITE+quote(directory, safe='/')+'/'
                self.send_header('Link', '<'+canonical+'>; rel="canonical"')
            else:
                self.send_header('X-Robots-Tag', 'noindex')
        if request_path in {'/llms.txt', '/llms-full.txt'}:
            self.send_header('X-Robots-Tag', 'noindex')
        super().end_headers()


if __name__ == '__main__':
    handler = partial(UTF8Handler, directory=str(ROOT))
    with ThreadingHTTPServer(('127.0.0.1', 4173), handler) as server:
        print('Serving PPW at http://127.0.0.1:4173 (UTF-8)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
