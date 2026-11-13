#!/usr/bin/env python3
"""Preview the static site with UTF-8, compression and safe asset caching."""
from datetime import timezone
from email.utils import parsedate_to_datetime
from functools import partial
import gzip
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from os import fstat
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://' + (ROOT/'CNAME').read_text(encoding='utf-8').strip() + '/'


class UTF8Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.md': 'text/markdown'}
    cacheable_assets = {'.css', '.js', '.woff2', '.png', '.jpg', '.jpeg', '.webp', '.avif', '.gif', '.svg', '.ico'}

    def accepts_gzip(self):
        preferences = {}
        for item in self.headers.get('Accept-Encoding', '').split(','):
            name, *parameters = item.strip().lower().split(';')
            quality = 1.0
            for parameter in parameters:
                if parameter.strip().startswith('q='):
                    try:
                        quality = float(parameter.strip()[2:])
                    except ValueError:
                        quality = 0.0
            preferences[name.strip()] = quality if 0 <= quality <= 1 else 0.0
        return preferences.get('gzip', preferences.get('*', 0)) > 0

    def send_head(self):
        self._cache_control = 'no-cache'
        request = urlsplit(self.path)
        trailing_slash = unquote(request.path).endswith('/')
        target = Path(self.translate_path(self.path))
        directory_index = False
        if target.is_dir() and trailing_slash:
            index_pages = getattr(self, 'index_pages', ('index.html', 'index.htm'))
            target = next((target/name for name in index_pages if (target/name).is_file()), target)
            directory_index = target.is_file()
        # Keep the standard directory redirects, listings and error responses.
        if not target.is_file() or trailing_slash and not directory_index:
            return super().send_head()
        try:
            with target.open('rb') as file:
                data = file.read()
                modified = fstat(file.fileno()).st_mtime
        except OSError:
            return super().send_head()

        digest = sha256(data).hexdigest()
        version = parse_qs(request.query).get('v')
        if target.suffix.lower() in self.cacheable_assets and version == [digest[:12]]:
            self._cache_control = 'public, max-age=31536000, immutable'

        content_type = self.guess_type(str(target))
        compressible = content_type.startswith('text/') or content_type.split(';')[0] in {
            'application/javascript', 'application/json', 'application/xml', 'image/svg+xml'
        }
        encoded = gzip.compress(data, mtime=0) if compressible and self.accepts_gzip() else data
        compressed = len(encoded) < len(data)
        body = encoded if compressed else data
        etag = '"' + sha256(body).hexdigest() + '"'

        not_modified = False
        if 'If-None-Match' in self.headers:
            candidates = (value.strip().removeprefix('W/') for value in self.headers['If-None-Match'].split(','))
            not_modified = any(value in {'*', etag} for value in candidates)
        elif 'If-Modified-Since' in self.headers:
            try:
                since = parsedate_to_datetime(self.headers['If-Modified-Since'])
                if since.tzinfo is None:
                    since = since.replace(tzinfo=timezone.utc)
                not_modified = int(modified) <= since.timestamp()
            except (TypeError, IndexError, OverflowError, ValueError):
                pass

        self.send_response(304 if not_modified else 200)
        self.send_header('Last-Modified', self.date_time_string(modified))
        self.send_header('ETag', etag)
        if compressible:
            self.send_header('Vary', 'Accept-Encoding')
        if not not_modified:
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            if compressed:
                self.send_header('Content-Encoding', 'gzip')
        self.end_headers()
        return None if not_modified else BytesIO(body)

    def guess_type(self, path):
        content_type = super().guess_type(path)
        if content_type.startswith('text/') or content_type in {
            'application/javascript', 'application/json', 'application/xml', 'image/svg+xml'
        }:
            return content_type + '; charset=utf-8'
        return content_type

    def end_headers(self):
        self.send_header('Cache-Control', getattr(self, '_cache_control', 'no-cache'))
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
