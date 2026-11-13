"""Release packaging contracts, including cross-deployment asset retention."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from asset_files import fingerprint_path
from package_pages import package


class PackagePagesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)/'repo'
        self.root.mkdir()
        self.output = Path(self.temporary.name)/'dist'
        self.write('index.html', b'<h1>Public</h1>')
        self.write('assets/asset-manifest.json', b'{"version":1,"assets":{},"sources":{}}')

    def write(self, name, data):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def git(self, *arguments):
        return subprocess.run(['git', '-C', str(self.root), *arguments],
                              check=True, capture_output=True).stdout

    def commit(self, message):
        self.git('add', '.')
        self.git('-c', 'user.name=Packaging test', '-c', 'user.email=packaging@example.invalid',
                 'commit', '-m', message)

    def test_only_public_files_are_packaged(self):
        public = {
            'CNAME': b'example.com', '.nojekyll': b'', 'google123.html': b'verification',
            '404.html': b'<h1>Page not found</h1>',
            'analytics.js': b'current', 'styles.min.css': b'body{}',
            'assets/fonts/dm-sans-OFL.txt': b'license',
            fingerprint_path('analytics.js', b'old'): b'old',
            'blog/article/index.html': b'article', 'blog/article/index.md': b'# Article',
            'blog/article/chart.svg': b'<svg/>', 'echipa/index.html': b'team',
        }
        excluded = {
            'README.md': b'private notes', 'styles.css': b'authored CSS',
            'docs/SEO.md': b'notes', 'scripts/build.py': b'build script',
            'node_modules/library/index.js': b'dependency', '.git/config': b'git config',
            'assets/private.json': b'not a public asset', 'assets/.git/config': b'nested config',
            'blog/article/draft.md': b'draft',
        }
        for name, data in {**public, **excluded}.items():
            self.write(name, data)
        package(self.root, self.output)
        for name, data in public.items():
            self.assertEqual((self.output/name).read_bytes(), data)
        for name in excluded:
            self.assertFalse((self.output/name).exists(), name)
        # Rebuilds replace old generated output, so stray files cannot leak later.
        (self.output/'stray.txt').write_text('stale')
        package(self.root, self.output)
        self.assertFalse((self.output/'stray.txt').exists())

    def test_history_preserves_changes_deleted_assets_and_same_byte_renames(self):
        self.git('init', '-b', 'main')
        old = b'old analytics bytes'
        image = b'image bytes'
        self.write('analytics.js', old)
        self.write('assets/old-logo.png', image)
        self.commit('Initial runtime assets')
        self.git('mv', 'assets/old-logo.png', 'assets/new-logo.png')
        self.write('analytics.js', b'new analytics bytes')
        self.commit('Update script and rename logo')
        (self.root/'assets/new-logo.png').unlink()
        self.commit('Remove current logo')
        retained = package(self.root, self.output, history=True)
        self.assertGreaterEqual(retained, 4)
        self.assertEqual((self.output/fingerprint_path('analytics.js', old)).read_bytes(), old)
        self.assertEqual((self.output/fingerprint_path('analytics.js', b'new analytics bytes')).read_bytes(),
                         b'new analytics bytes')
        self.assertEqual((self.output/fingerprint_path('assets/old-logo.png', image)).read_bytes(), image)
        self.assertEqual((self.output/fingerprint_path('assets/new-logo.png', image)).read_bytes(), image)

    def test_history_excludes_unmerged_branch_assets(self):
        self.git('init', '-b', 'main')
        self.write('analytics.js', b'public')
        self.commit('Public assets')
        self.git('checkout', '-b', 'unreleased')
        self.write('assets/unreleased.png', b'unreleased image')
        self.commit('Unreleased image')
        self.git('checkout', 'main')
        package(self.root, self.output, history=True)
        self.assertFalse((self.output/fingerprint_path('assets/unreleased.png', b'unreleased image')).exists())

    def test_history_retains_merge_resolution_without_branch_only_versions(self):
        self.git('init', '-b', 'main')
        self.write('analytics.js', b'initial')
        self.commit('Initial assets')
        self.git('checkout', '-b', 'feature')
        self.write('analytics.js', b'branch only')
        self.commit('Feature script')
        self.git('checkout', 'main')
        self.write('analytics.js', b'main before merge')
        self.commit('Main script')
        result = subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Packaging test',
                                 '-c', 'user.email=packaging@example.invalid',
                                 'merge', '--no-commit', 'feature'], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.write('analytics.js', b'merge resolution')
        self.commit('Resolve script merge')
        self.write('analytics.js', b'current')
        self.commit('Latest script')
        package(self.root, self.output, history=True)
        self.assertEqual((self.output/fingerprint_path('analytics.js', b'merge resolution')).read_bytes(),
                         b'merge resolution')
        self.assertFalse((self.output/fingerprint_path('analytics.js', b'branch only')).exists())

    def test_missing_history_fails_instead_of_dropping_older_assets(self):
        with self.assertRaisesRegex(RuntimeError, 'Git asset history failed'):
            package(self.root, self.output, history=True)
        self.assertFalse(self.output.exists())

    def test_cannot_replace_source_or_an_unowned_output(self):
        with self.assertRaisesRegex(ValueError, 'separate build directory'):
            package(self.root, self.root)
        with self.assertRaisesRegex(ValueError, 'separate build directory'):
            package(self.root, self.root/'assets/dist')
        self.output.mkdir()
        (self.output/'important.txt').write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'not created by this packager'):
            package(self.root, self.output)
        self.assertEqual((self.output/'important.txt').read_text(), 'preserve')

    def test_modified_generated_asset_fails_before_replacing_output(self):
        self.write(fingerprint_path('analytics.js', b'original'), b'modified')
        with self.assertRaisesRegex(ValueError, 'Invalid generated asset fingerprint'):
            package(self.root, self.output)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
