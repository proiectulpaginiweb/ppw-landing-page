"""Exercise preview HTTP cache behavior for physical and legacy asset versions."""
from functools import partial
import gzip
from hashlib import sha256
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import serve


IMMUTABLE = 'public, max-age=31536000, immutable'


class QuietHandler(serve.UTF8Handler):
    def log_message(self, *args):
        pass


class CacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory(prefix='ppw-cache-test-')
        cls.root = Path(cls.directory.name)
        cls.old = b'const message = "old deployment";\n' * 100
        cls.current = b'const message = "new deployment";\n' * 100
        cls.old_hash = sha256(cls.old).hexdigest()[:12]
        cls.current_hash = sha256(cls.current).hexdigest()[:12]
        folder = cls.root/'assets/static'
        folder.mkdir(parents=True)
        cls.old_path = f'/assets/static/script.{cls.old_hash}.js'
        cls.current_path = f'/assets/static/script.{cls.current_hash}.js'
        (cls.root/cls.old_path.lstrip('/')).write_bytes(cls.old)
        (cls.root/cls.current_path.lstrip('/')).write_bytes(cls.current)
        (folder/'script.000000000000.js').write_bytes(cls.current)
        nested = folder/'assets/fonts'
        nested.mkdir(parents=True)
        cls.nested_path = f'/assets/static/assets/fonts/font.{cls.current_hash}.woff2'
        (cls.root/cls.nested_path.lstrip('/')).write_bytes(cls.current)
        (cls.root/'script.js').write_bytes(cls.current)
        (cls.root/f'script.{cls.current_hash}.js').write_bytes(cls.current)
        cls.html = b'<!doctype html><html lang="ro"><title>PPW</title></html>'
        (cls.root/'index.html').write_bytes(cls.html)
        cls.root_patch = patch.object(serve, 'ROOT', cls.root)
        cls.root_patch.start()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(cls.root)))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.root_patch.stop()
        cls.directory.cleanup()

    def request(self, path, headers=None, method='GET'):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_old_and_new_fingerprints_keep_their_own_bytes(self):
        for path, expected in ((self.old_path, self.old), (self.current_path, self.current)):
            with self.subTest(path=path):
                status, headers, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertEqual(body, expected)
                self.assertEqual(headers['Cache-Control'], IMMUTABLE)

    def test_only_matching_physical_fingerprints_get_long_caching(self):
        for path in ('/assets/static/script.000000000000.js',
                     f'/script.{self.current_hash}.js', '/script.js'):
            with self.subTest(path=path):
                status, headers, _ = self.request(path)
                self.assertEqual(status, 200)
                self.assertEqual(headers['Cache-Control'], 'no-cache')

    def test_nested_fingerprints_receive_the_same_long_cache_lifetime(self):
        status, headers, body = self.request(self.nested_path)
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], IMMUTABLE)
        self.assertEqual(body, self.current)

    def test_legacy_query_version_must_match_the_actual_bytes(self):
        for version, expected in ((self.current_hash, IMMUTABLE), (self.old_hash, 'no-cache'),
                                  ('wrong', 'no-cache'), (self.current_hash+'&v=wrong', 'no-cache')):
            with self.subTest(version=version):
                status, headers, _ = self.request('/script.js?v='+version)
                self.assertEqual(status, 200)
                self.assertEqual(headers['Cache-Control'], expected)

    def test_html_revalidates_even_with_its_content_hash_in_the_query(self):
        for path in ('/', '/index.html?v='+sha256(self.html).hexdigest()[:12]):
            with self.subTest(path=path):
                status, headers, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertEqual(body, self.html)
                self.assertEqual(headers['Cache-Control'], 'no-cache')

    def test_gzip_and_conditional_responses_keep_the_cache_policy(self):
        status, headers, body = self.request(self.current_path, {'Accept-Encoding': 'gzip'})
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Encoding'], 'gzip')
        self.assertEqual(headers['Vary'], 'Accept-Encoding')
        self.assertEqual(headers['Cache-Control'], IMMUTABLE)
        self.assertEqual(gzip.decompress(body), self.current)

        status, cached_headers, body = self.request(self.current_path, {
            'Accept-Encoding': 'gzip', 'If-None-Match': headers['ETag'],
        })
        self.assertEqual(status, 304)
        self.assertEqual(body, b'')
        self.assertEqual(cached_headers['ETag'], headers['ETag'])
        self.assertEqual(cached_headers['Vary'], 'Accept-Encoding')
        self.assertEqual(cached_headers['Cache-Control'], IMMUTABLE)

        status, _, plain_body = self.request(self.current_path, {'If-None-Match': headers['ETag']})
        self.assertEqual(status, 200)
        self.assertEqual(plain_body, self.current)

    def test_head_and_last_modified_validation_preserve_headers(self):
        status, headers, body = self.request(self.old_path, method='HEAD')
        self.assertEqual(status, 200)
        self.assertEqual(body, b'')
        self.assertEqual(int(headers['Content-Length']), len(self.old))
        self.assertEqual(headers['Cache-Control'], IMMUTABLE)

        status, cached_headers, body = self.request(self.old_path, {
            'If-Modified-Since': headers['Last-Modified'],
        })
        self.assertEqual(status, 304)
        self.assertEqual(body, b'')
        self.assertEqual(cached_headers['Cache-Control'], IMMUTABLE)

    def test_missing_fingerprint_does_not_get_long_caching(self):
        status, headers, _ = self.request('/assets/static/missing.123456789abc.js')
        self.assertEqual(status, 404)
        self.assertEqual(headers['Cache-Control'], 'no-cache')


if __name__ == '__main__':
    unittest.main()
