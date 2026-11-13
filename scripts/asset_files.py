"""Content-addressed public assets; stable authored paths stay editable."""
from hashlib import sha256
from html import escape, unescape
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

ASSET_DIRECTORY = 'assets/static'
MANIFEST = 'assets/asset-manifest.json'
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.avif', '.gif', '.svg', '.ico'}
FINGERPRINT = re.compile(r'\.([0-9a-f]{12})\.[^.]+$')


def fingerprint_path(source, data):
    path = Path(source)
    return (Path(ASSET_DIRECTORY)/path.parent/
            f'{path.stem}.{sha256(data).hexdigest()[:12]}{path.suffix}').as_posix()


def is_fingerprinted_asset(path, root, data):
    try:
        relative = path.resolve().relative_to((root/ASSET_DIRECTORY).resolve())
    except ValueError:
        return False
    match = FINGERPRINT.search(relative.name)
    return bool(match) and match[1] == sha256(data).hexdigest()[:12]


def asset_sources(root):
    sources = [root/name for name in ('script.js', 'blog.js', 'analytics.js')]
    sources.extend(path for path in (root/'assets').rglob('*')
                   if path.is_file() and path.relative_to(root).parts[:2] != ('assets', 'static')
                   and path.suffix.lower() in IMAGE_EXTENSIONS | {'.woff2'})
    sources.extend((root/'blog').rglob('*.svg'))
    return sorted(set(sources))


class AssetCatalog:
    def __init__(self, root, site='https://www.proiectulpaginiweb.ro/'):
        self.root = Path(root).resolve()
        self.site = site
        self.assets = {}
        self.sources = {}
        manifest = self.root/MANIFEST
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding='utf-8'))
            if data.get('version') != 1:
                raise ValueError('Unsupported asset manifest version')
            self.assets = data['assets']
            self.sources = data['sources']

    def generate(self):
        current = {}
        for source in asset_sources(self.root):
            logical = source.relative_to(self.root).as_posix()
            data = source.read_bytes()
            generated = fingerprint_path(logical, data)
            destination = self.root/generated
            destination.parent.mkdir(parents=True, exist_ok=True)
            # A published fingerprint must never change its bytes.
            if destination.exists():
                if destination.read_bytes() != data:
                    raise ValueError('Fingerprint collision or modified generated asset: '+generated)
            else:
                destination.write_bytes(data)
            current[logical] = generated
            self.sources[generated] = logical
        self.assets = current
        (self.root/MANIFEST).write_text(json.dumps({
            'version': 1, 'assets': self.assets, 'sources': self.sources,
        }, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')

    def reference(self, reference, page, hashed=True):
        try:
            parsed = urlsplit(reference)
        except ValueError:
            return reference
        if parsed.scheme and parsed.scheme not in {'http', 'https'}:
            return reference
        if parsed.netloc and parsed.hostname not in {
            urlsplit(self.site).hostname, urlsplit(self.site).hostname.removeprefix('www.'),
        }:
            return reference
        if not parsed.path:
            return reference
        path = unquote(parsed.path)
        target = ((self.root/path.lstrip('/')) if path.startswith('/')
                  else (page.parent/path)).resolve()
        if not target.is_relative_to(self.root):
            return reference
        logical = target.relative_to(self.root).as_posix()
        logical = self.sources.get(logical, logical)
        if logical not in self.assets:
            return reference
        destination = self.assets[logical] if hashed else logical
        if parsed.netloc or path.startswith('/'):
            destination = '/'+destination
        else:
            parent = page.parent.relative_to(self.root).as_posix()
            destination = posixpath.relpath(destination, parent)
        query = urlencode([(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                           if key != 'v'])
        return urlunsplit((parsed.scheme, parsed.netloc, destination, query, parsed.fragment))

    def rewrite_html(self, source, page, hashed=True):
        def schema(match):
            def rewrite(value):
                if isinstance(value, str):
                    return self.reference(value, page, hashed)
                if isinstance(value, list):
                    return [rewrite(item) for item in value]
                if isinstance(value, dict):
                    return {key: rewrite(item) for key, item in value.items()}
                return value
            value = rewrite(json.loads(match[2]))
            return match[1]+json.dumps(value, ensure_ascii=False, indent=2).replace('</', '<\\/')+match[3]
        source = re.sub(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
                        schema, source, flags=re.S | re.I)

        def attribute(match):
            value = unescape(match[3])
            updated = self.reference(value, page, hashed)
            return match[0] if updated == value else match[1]+match[2]+escape(updated, quote=True)+match[2]
        source = re.sub(r'(\b(?:src|href|poster|content)\s*=\s*)(["\'])(.*?)\2',
                        attribute, source, flags=re.S | re.I)

        def srcset(match):
            value = unescape(match[3])
            if value.lstrip().startswith('data:'):
                return match[0]
            candidates = []
            for candidate in value.split(','):
                parts = candidate.strip().split(maxsplit=1)
                if parts:
                    candidates.append(self.reference(parts[0], page, hashed)+
                                      (' '+parts[1] if len(parts) > 1 else ''))
            return match[1]+match[2]+escape(', '.join(candidates), quote=True)+match[2]
        return re.sub(r'(\bsrcset\s*=\s*)(["\'])(.*?)\2', srcset, source, flags=re.S | re.I)


if __name__ == '__main__':
    catalog = AssetCatalog(Path(__file__).resolve().parent.parent)
    catalog.generate()
    print(f'Generated {len(catalog.assets)} fingerprinted assets; older files retained.')
