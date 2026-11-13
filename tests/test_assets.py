"""Exercise asset changes through the real build, including existing hashed HTML."""
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class AssetBuildTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='ppw-assets-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)/'site'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', 'dist'))
        (self.root/'node_modules').symlink_to(ROOT/'node_modules', target_is_directory=True)
        self.build()

    def build(self):
        result = subprocess.run(['npm', 'run', 'build'], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        return json.loads((self.root/'assets/asset-manifest.json').read_text())['assets']

    def pages(self):
        return [self.root/'index.html', self.root/'404.html', self.root/'echipa/index.html',
                self.root/'blog/index.html', *sorted((self.root/'blog').glob('*/index.html'))]

    def snapshot(self):
        paths = [*self.pages(), *self.root.glob('*.min.css'), *self.root.rglob('index.md'),
                 self.root/'assets/asset-manifest.json', self.root/'llms-full.txt', self.root/'llms.txt']
        return {path.relative_to(self.root).as_posix(): sha256(path.read_bytes()).hexdigest() for path in paths}

    def test_repeat_build_is_identical_and_assets_match_their_names(self):
        before = self.snapshot()
        assets = self.build()
        self.assertEqual(before, self.snapshot())
        for logical, generated in assets.items():
            data = (self.root/generated).read_bytes()
            self.assertEqual(data, (self.root/logical).read_bytes())
            self.assertIn('.'+sha256(data).hexdigest()[:12]+'.', generated)
        for page in self.pages():
            source = page.read_text()
            self.assertNotRegex(source, r'\?v=[0-9a-f]{12}')
            css_urls = set(re.findall(r'url\(["\']?([^\)"\']+)', source))
            preloads = re.findall(r'<link rel="preload" href="([^"]+)"', source)
            self.assertEqual(len(preloads), 4)
            self.assertTrue(set(preloads) <= css_urls)
            for reference in preloads:
                target = self.root/reference.lstrip('/') if reference.startswith('/') else page.parent/reference
                self.assertTrue(target.is_file())
        error_page = (self.root/'404.html').read_text()
        self.assertIn('content="noindex, follow"', error_page)
        self.assertNotIn('/404.html', (self.root/'sitemap.xml').read_text())
        homepage = (self.root/'index.html').read_text()
        self.assertIn(assets['assets/proiectul-pagini-web-logo-2013.webp'], homepage)
        self.assertIn(assets['assets/proiectul-pagini-web-logo-2013.png'], homepage)

    def test_changed_script_updates_every_page_and_preserves_old_file(self):
        before = self.build()
        original = (self.root/before['analytics.js']).read_bytes()
        with (self.root/'analytics.js').open('a') as file:
            file.write('\n// A new deployment with a changed analytics asset.\n')
        after = self.build()
        self.assertNotEqual(before['analytics.js'], after['analytics.js'])
        self.assertEqual((self.root/before['analytics.js']).read_bytes(), original)
        for logical in before.keys()-{'analytics.js'}:
            self.assertEqual(before[logical], after[logical], logical)
        for page in self.pages():
            self.assertIn(Path(after['analytics.js']).name, page.read_text())
            self.assertNotIn(Path(before['analytics.js']).name, page.read_text())

    def test_changed_media_updates_html_schema_and_exports(self):
        before = self.build()
        chart = self.root/'blog/spring-rails-react-tokeni-startup/tokeni-cod.svg'
        chart.write_text(chart.read_text().replace('</svg>', '<!-- new chart version --></svg>'))
        portrait = self.root/'assets/sarbull.jpg'
        data = portrait.read_bytes()
        self.assertEqual(data[:2], b'\xff\xd8')
        # A legal JPEG comment changes the bytes while retaining the image data.
        portrait.write_bytes(data[:2]+b'\xff\xfe\x00\x07cache'+data[2:])
        after = self.build()
        for logical in ('blog/spring-rails-react-tokeni-startup/tokeni-cod.svg', 'assets/sarbull.jpg'):
            self.assertNotEqual(before[logical], after[logical])
            self.assertTrue((self.root/before[logical]).is_file())
        self.assertIn(after['blog/spring-rails-react-tokeni-startup/tokeni-cod.svg'],
                      (self.root/'llms-full.txt').read_text())
        article = (chart.parent/'index.html').read_text()
        self.assertIn(after['blog/spring-rails-react-tokeni-startup/tokeni-cod.svg'], article)
        self.assertIn(after['assets/sarbull.jpg'], (self.root/'echipa/index.html').read_text())
        self.assertNotIn(before['assets/sarbull.jpg'], (self.root/'echipa/index.html').read_text())
        self.assertIn(after['blog/spring-rails-react-tokeni-startup/tokeni-cod.svg'],
                      (chart.parent/'index.md').read_text())

    def test_corrupted_existing_fingerprint_is_not_overwritten(self):
        assets = self.build()
        target = self.root/assets['analytics.js']
        target.write_bytes(b'corrupted historical asset')
        result = subprocess.run(['npm', 'run', 'build'], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('modified generated asset', result.stderr)
        self.assertEqual(target.read_bytes(), b'corrupted historical asset')

    def test_identical_basenames_in_different_folders_update_independently(self):
        for directory in ('one', 'two'):
            path = self.root/'assets'/directory/'shared.svg'
            path.parent.mkdir()
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        page = self.root/'index.html'
        page.write_text(page.read_text().replace('</main>',
            '<img src="assets/one/shared.svg" width="1" height="1" alt="" />'
            '<img src="assets/two/shared.svg" width="1" height="1" alt="" /></main>'))
        before = self.build()
        self.assertNotEqual(before['assets/one/shared.svg'], before['assets/two/shared.svg'])
        path = self.root/'assets/one/shared.svg'
        path.write_text(path.read_text().replace('</svg>', '<!-- changed --></svg>'))
        after = self.build()
        self.assertNotEqual(before['assets/one/shared.svg'], after['assets/one/shared.svg'])
        self.assertEqual(before['assets/two/shared.svg'], after['assets/two/shared.svg'])
        self.assertIn(after['assets/one/shared.svg'], page.read_text())
        self.assertIn(after['assets/two/shared.svg'], page.read_text())


if __name__ == '__main__':
    unittest.main()
