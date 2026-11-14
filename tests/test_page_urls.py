"""Keep published links usable when canonical page URLs move to Romanian."""
from functools import partial
from html.parser import HTMLParser
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from package_pages import package
from page_urls import PAGE_REDIRECTS, FRAGMENT_REDIRECTS, redirect_target, write_redirect_pages
import serve

SITE = 'https://www.proiectulpaginiweb.ro/'


class RedirectPage(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.scripts = []
        self.in_script = False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        if tag == 'script':
            self.in_script = True
            self.scripts.append('')

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False

    def handle_data(self, value):
        if self.in_script:
            self.scripts[-1] += value


class PageURLTests(unittest.TestCase):
    def test_only_known_legacy_routes_redirect(self):
        for old, new in PAGE_REDIRECTS.items():
            for suffix, expected in (('', new), ('index.html', new), ('index.md', new+'index.md')):
                with self.subTest(old=old, suffix=suffix):
                    self.assertEqual(redirect_target(old+suffix), expected)
            self.assertEqual(redirect_target(old.rstrip('/')), new)
            for path in (new, new+'index.html', old+'arbitrary.html', old+'extra/',
                         '/unrelated'+old, old.rstrip('/')+'-extra/'):
                self.assertIsNone(redirect_target(path), path)

    def test_canonical_sources_and_discovery_use_the_new_routes(self):
        sitemap = (ROOT/'sitemap.xml').read_text(encoding='utf-8')
        directory = (ROOT/'llms.txt').read_text(encoding='utf-8')
        for old, new in PAGE_REDIRECTS.items():
            self.assertFalse((ROOT/old.lstrip('/')/'index.html').exists(), old)
            self.assertTrue((ROOT/new.lstrip('/')/'index.html').is_file(), new)
            for source in (sitemap, directory):
                self.assertIn(SITE+new.lstrip('/'), source)
                self.assertNotIn(SITE+old.lstrip('/'), source)

    def test_packaging_adds_migration_pages_without_duplicate_article_sources(self):
        with TemporaryDirectory(prefix='ppw-url-package-') as temporary:
            root = Path(temporary)/'repo'
            root.mkdir()
            (root/'index.html').write_text('<h1>PPW</h1>', encoding='utf-8')
            (root/'CNAME').write_text('www.proiectulpaginiweb.ro\n', encoding='utf-8')
            (root/'assets').mkdir()
            (root/'assets/asset-manifest.json').write_text(
                '{"version":1,"assets":{},"sources":{}}', encoding='utf-8')
            for new in PAGE_REDIRECTS.values():
                page = root/new.lstrip('/')
                page.mkdir(parents=True)
                (page/'index.html').write_text('<h1>Articol</h1>', encoding='utf-8')
                (page/'index.md').write_text('# Articol\n', encoding='utf-8')
            output = Path(temporary)/'dist'
            package(root, output)
            for old, new in PAGE_REDIRECTS.items():
                self.assertFalse((root/old.lstrip('/')).exists())
                source = (output/old.lstrip('/')/'index.html').read_text(encoding='utf-8')
                page = RedirectPage(source)
                canonical = SITE+new.lstrip('/')
                self.assertIn(('link', {'rel': 'canonical', 'href': canonical}), page.elements)
                self.assertTrue(any(tag == 'meta' and attrs.get('name') == 'robots'
                                    and 'noindex' in attrs.get('content', '')
                                    for tag, attrs in page.elements))
                self.assertTrue(any(tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh'
                                    and canonical in attrs.get('content', '')
                                    for tag, attrs in page.elements))
                self.assertTrue(any(tag == 'a' and attrs.get('href') == canonical
                                    for tag, attrs in page.elements))
                self.assertEqual((output/new.lstrip('/')/'index.html').read_text(), '<h1>Articol</h1>')
                notice = (output/old.lstrip('/')/'index.md').read_text(encoding='utf-8')
                self.assertIn(canonical, notice)
                self.assertIn(canonical+'index.md', notice)

    def test_static_redirect_preserves_query_and_section_links(self):
        with TemporaryDirectory(prefix='ppw-url-script-') as temporary:
            output = Path(temporary)
            for new in PAGE_REDIRECTS.values():
                destination = output/new.lstrip('/')
                destination.mkdir(parents=True)
                (destination/'index.html').write_text('<h1>Articol</h1>')
                (destination/'index.md').write_text('# Articol')
            write_redirect_pages(output, SITE)
            cases = []
            for old, new in PAGE_REDIRECTS.items():
                page = RedirectPage((output/old.lstrip('/')/'index.html').read_text(encoding='utf-8'))
                script = '\n'.join(page.scripts)
                fragments = FRAGMENT_REDIRECTS.get(new, {})
                for original, translated in [('', ''), ('pe-scurt', 'pe-scurt'), *fragments.items()]:
                    query = '?sursa=buletin&campanie=toamna%202026'
                    fragment = '#'+original if original else ''
                    expected = SITE+new.lstrip('/')+query+('#'+translated if translated else '')
                    cases.append({'script': script, 'path': old, 'query': query,
                                  'hash': fragment, 'expected': expected})
            program = r'''
const fs = require('node:fs');
const vm = require('node:vm');
for (const entry of JSON.parse(fs.readFileSync(0, 'utf8'))) {
  let actual;
  const location = { pathname: entry.path, search: entry.query, hash: entry.hash,
    href: 'https://www.proiectulpaginiweb.ro'+entry.path+entry.query+entry.hash,
    replace(value) { actual = String(value); } };
  vm.runInNewContext(entry.script, {location, window: {location}, URL});
  if (actual !== entry.expected) {
    throw new Error(JSON.stringify({actual, expected: entry.expected, path: entry.path}));
  }
}
'''
            result = subprocess.run(['node', '-e', program], input=json.dumps(cases),
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)


    def test_canonical_article_updates_legacy_fragments_and_scrolls_to_the_section(self):
        script = (ROOT/'blog.js').read_text(encoding='utf-8')
        cases = []
        for path, fragments in FRAGMENT_REDIRECTS.items():
            article = RedirectPage((ROOT/path.lstrip('/')/'index.html').read_text(encoding='utf-8'))
            headings = [{'old': attrs['data-ancora-veche'], 'id': attrs['id']}
                        for _, attrs in article.elements if 'data-ancora-veche' in attrs]
            self.assertEqual({heading['old']: heading['id'] for heading in headings}, fragments)
            for old, new in [*fragments.items(), ('pe-scurt', None)]:
                cases.append({'path': path, 'headings': headings, 'old': old, 'new': new})
        program = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const entry of input.cases) {
  let replaced = null, scrolled = null;
  const listeners = {};
  const headings = entry.headings.map(heading => ({
    id: heading.id, dataset: {ancoraVeche: heading.old},
    scrollIntoView() { scrolled = heading.id; }
  }));
  const menu = { addEventListener() {}, setAttribute() {}, getAttribute() { return 'false'; } };
  const navigation = { querySelectorAll() { return []; }, classList: {remove() {}, toggle() {}} };
  const document = {
    querySelector(selector) { return selector === '.menu-toggle' ? menu : navigation; },
    querySelectorAll() { return headings; }, addEventListener() {}
  };
  const location = {pathname: entry.path, search: '?sursa=buletin', hash: '#'+entry.old};
  vm.runInNewContext(input.script, {document, location,
    history: {replaceState(_, __, value) { replaced = value; }},
    window: {addEventListener(name, callback) { listeners[name] = callback; }} });
  const expected = entry.new ? entry.path+'?sursa=buletin#'+entry.new : null;
  if (replaced !== expected || scrolled !== entry.new) {
    throw new Error(JSON.stringify({entry, replaced, scrolled, expected}));
  }
  if (typeof listeners.hashchange !== 'function') throw new Error('Missing hashchange listener');
  if (entry.new) {
    replaced = null; scrolled = null;
    listeners.hashchange();
    if (replaced !== expected || scrolled !== entry.new) throw new Error('Hashchange did not migrate');
  }
}
'''
        result = subprocess.run(['node', '-e', program], input=json.dumps({'script': script, 'cases': cases}),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class QuietHandler(serve.UTF8Handler):
    def log_message(self, *args):
        pass


class PageURLHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory(prefix='ppw-url-http-')
        cls.root = Path(cls.directory.name)
        for new in PAGE_REDIRECTS.values():
            destination = cls.root/new.lstrip('/')
            destination.mkdir(parents=True)
            (destination/'index.html').write_text('<h1>Articol</h1>')
            (destination/'index.md').write_text('# Articol')
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

    def test_legacy_http_aliases_redirect_directly_with_query_preserved(self):
        query = '?sursa=buletin&campanie=toamna%202026'
        for old, new in PAGE_REDIRECTS.items():
            for path, destination in ((old, new), (old.rstrip('/'), new),
                                      (old+'index.html', new), (old+'index.md', new+'index.md')):
                for method in ('GET', 'HEAD'):
                    with self.subTest(path=path, method=method):
                        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
                        try:
                            connection.request(method, path+query)
                            response = connection.getresponse()
                            self.assertEqual(response.status, 301)
                            self.assertEqual(response.getheader('Location'), destination+query)
                            self.assertEqual(response.read(), b'')
                        finally:
                            connection.close()


if __name__ == '__main__':
    unittest.main()
