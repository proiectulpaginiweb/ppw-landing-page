#!/usr/bin/env python3
"""Package public files for Pages, optionally retaining assets from Git history."""
import argparse
from collections import defaultdict
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile

from asset_files import (ASSET_DIRECTORY, IMAGE_EXTENSIONS, MANIFEST,
                         fingerprint_path, is_fingerprinted_asset)
from page_urls import write_redirect_pages


ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = (
    'index.html', '404.html', 'index.md', 'robots.txt', 'sitemap.xml', 'llms.txt', 'llms-full.txt',
    'script.js', 'blog.js', 'analytics.js', 'CNAME', '.nojekyll',
    'styles.min.css', 'home.min.css', 'blog.min.css', 'echipa.min.css',
)
PAGE_DIRECTORIES = ('blog', 'echipa')
BUILD_MARKER = '.ppw-pages-build'
IGNORED_PARTS = {'.git', '.github', 'node_modules', '__pycache__'}


def historical_source(name):
    """Only public runtime asset sources, never generated files or other branches."""
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or IGNORED_PARTS.intersection(path.parts):
        return False
    if name in {'script.js', 'blog.js', 'analytics.js'}:
        return True
    if name.startswith(ASSET_DIRECTORY+'/'):
        return False
    if path.parts and path.parts[0] == 'assets':
        return path.suffix.lower() in IMAGE_EXTENSIONS | {'.woff2'}
    return bool(path.parts) and path.parts[0] == 'blog' and path.suffix.lower() == '.svg'


def git(root, *arguments):
    result = subprocess.run(['git', '-C', str(root), *arguments],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError('Git asset history failed: '+result.stderr.decode(errors='replace').strip())
    return result.stdout


def history_objects(root):
    """Collect path/blob pairs, including unchanged-content renames and deletions."""
    if git(root, 'rev-parse', '--is-shallow-repository').strip() != b'false':
        raise RuntimeError('Asset retention needs full Git history; use checkout fetch-depth: 0.')
    # The first-parent timeline contains earlier deployments of this branch.
    # Diff merges against their first parent to retain merge-resolution bytes,
    # without publishing intermediate assets that never reached this branch.
    records = git(root, 'log', '--first-parent', '--diff-merges=first-parent',
                  '--format=', '--raw', '--no-abbrev', '--no-renames', '-z', 'HEAD').split(b'\0')
    objects = defaultdict(set)
    index = 0
    while index < len(records):
        header = records[index].strip()
        index += 1
        if not header.startswith(b':'):
            continue
        if index >= len(records):
            raise RuntimeError('Incomplete Git history record.')
        name = records[index].decode('utf-8')
        index += 1
        if not historical_source(name):
            continue
        fields = header[1:].split()
        if len(fields) != 5:
            raise RuntimeError('Unexpected Git asset history record.')
        old_mode, new_mode, old_object, new_object, _ = fields
        for mode, object_id in ((old_mode, old_object), (new_mode, new_object)):
            if mode in {b'100644', b'100755'} and object_id.strip(b'0'):
                objects[object_id.decode('ascii')].add(name)
    return objects


def retain_history(root, output):
    objects = history_objects(root)
    retained = 0
    process = subprocess.Popen(['git', '-C', str(root), 'cat-file', '--batch'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for object_id, sources in sorted(objects.items()):
            process.stdin.write(object_id.encode('ascii')+b'\n')
            process.stdin.flush()
            header = process.stdout.readline().strip().split()
            if len(header) != 3 or header[1] != b'blob':
                raise RuntimeError('Historical asset is not a readable Git blob: '+object_id)
            size = int(header[2])
            data = process.stdout.read(size)
            if len(data) != size or process.stdout.read(1) != b'\n':
                raise RuntimeError('Incomplete historical asset: '+object_id)
            for source in sorted(sources):
                destination = output/fingerprint_path(source, data)
                if destination.exists():
                    if destination.read_bytes() != data:
                        raise RuntimeError('Conflicting fingerprint bytes: '+str(destination))
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                retained += 1
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()
    if process.returncode:
        raise RuntimeError('git cat-file failed while restoring historical assets.')
    return retained


def public_files(root):
    for name in ROOT_FILES:
        path = root/name
        if path.is_file():
            yield path
    yield from sorted(root.glob('google*.html'))
    assets = root/'assets'
    for path in sorted(assets.rglob('*')):
        relative = path.relative_to(root)
        if IGNORED_PARTS.intersection(relative.parts) or not path.is_file():
            continue
        if (path.suffix.lower() in IMAGE_EXTENSIONS | {'.woff2'} or
                relative.as_posix() == MANIFEST or
                path.parent == assets/'fonts' and path.name.endswith('-OFL.txt') or
                relative.as_posix().startswith(ASSET_DIRECTORY+'/') and path.suffix in {'.js', '.css'}):
            yield path
    for directory in PAGE_DIRECTORIES:
        for path in sorted((root/directory).rglob('*')):
            if not path.is_file() or IGNORED_PARTS.intersection(path.relative_to(root).parts):
                continue
            if path.name in {'index.html', 'index.md'} or path.suffix.lower() in IMAGE_EXTENSIONS:
                yield path


def package(root, output, history=False):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or root.is_relative_to(output) or any(
            output.is_relative_to(root/directory) for directory in ('assets', 'blog', 'echipa', 'scripts', '.git')):
        raise ValueError('Pages output must be a separate build directory.')
    if not (root/'index.html').is_file() or not (root/MANIFEST).is_file():
        raise ValueError('Build the site first with npm run build before packaging Pages.')
    if output.exists() and any(output.iterdir()) and not (output/BUILD_MARKER).is_file():
        raise ValueError('Refusing to replace a nonempty directory not created by this packager: '+str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ppw-pages-', dir=output.parent) as temporary:
        staging = Path(temporary)/'site'
        staging.mkdir()
        for path in public_files(root):
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('Public files must not be symbolic links: '+str(path))
            if path.relative_to(root).as_posix().startswith(ASSET_DIRECTORY+'/') and not \
                    is_fingerprinted_asset(path, root, path.read_bytes()):
                raise ValueError('Invalid generated asset fingerprint: '+str(path))
            destination = staging/path.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
        retained = retain_history(root, staging) if history else 0
        hostname = (root/'CNAME').read_text(encoding='utf-8').strip() if (root/'CNAME').is_file() else 'www.proiectulpaginiweb.ro'
        write_redirect_pages(staging, 'https://'+hostname+'/')
        (staging/'.nojekyll').touch()
        (staging/BUILD_MARKER).write_text('Generated by scripts/package_pages.py\n', encoding='utf-8')
        if output.exists():
            shutil.rmtree(output)
        staging.rename(output)
    return retained


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=None)
    parser.add_argument('--history', action='store_true', help='retain historical assets from full HEAD ancestry')
    arguments = parser.parse_args()
    try:
        retained = package(arguments.root, arguments.output or arguments.root/'dist', arguments.history)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, str(error)+'\n')
    print(f'GitHub Pages package ready: {arguments.output or arguments.root/"dist"}; '
          f'{retained} historical asset files retained.')


if __name__ == '__main__':
    main()
