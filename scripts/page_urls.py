"""Keep old page addresses working after the Romanian URL migration."""
from html import escape
import json
from pathlib import Path
from urllib.parse import urljoin


PAGE_REDIRECTS = {
    '/blog/chat-ai-vs-agent-ai/': '/blog/diferenta-dintre-chat-ia-si-agent-ia/',
    '/blog/training-ai-models-for-specific-businesses/': '/blog/antrenarea-modelelor-ia-pentru-afaceri/',
    '/blog/spring-rails-react-tokeni-startup/': '/blog/java-ruby-javascript-costuri-tokeni-mvp/',
    '/blog/indexare-site-chatgpt-ai-geo/': '/blog/indexare-site-chatgpt-ia-geo/',
}
FRAGMENT_REDIRECTS = {
    '/blog/java-ruby-javascript-costuri-tokeni-mvp/': {
        'stackuri': 'tehnologii',
    },
    '/blog/antrenarea-modelelor-ia-pentru-afaceri/': {
        'business-context': 'contextul-afacerii',
        'training': 'antrenare',
        'applications': 'aplicatii',
        'feedback': 'imbunatatire-continua',
        'opportunity': 'abordarea-noastra',
    },
}


def redirect_target(request_path):
    """Return a new path for a legacy page; callers preserve query strings."""
    for previous, current in PAGE_REDIRECTS.items():
        if request_path in {previous.rstrip('/'), previous, previous+'index.html'}:
            return current
        if request_path == previous+'index.md':
            return current+'index.md'
    return None


def script_json(value):
    """JSON safe to embed in an HTML script element."""
    return (json.dumps(value, ensure_ascii=True).replace('&', '\\u0026')
            .replace('<', '\\u003c').replace('>', '\\u003e'))


def write_redirect_pages(output, site):
    """Write HTML fallbacks and Markdown notices only into a packaged site."""
    output = Path(output)
    for previous, current in PAGE_REDIRECTS.items():
        canonical = urljoin(site, current)
        fragments = FRAGMENT_REDIRECTS.get(current, {})
        destination = output/previous.lstrip('/')
        destination.mkdir(parents=True, exist_ok=True)
        html = f'''<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Articol mutat — Proiectul Pagini Web</title>
<meta name="robots" content="noindex, follow" />
<link rel="canonical" href="{escape(canonical, quote=True)}" />
<meta http-equiv="refresh" content="0; url={escape(canonical, quote=True)}" />
<script>
const target = new URL({script_json(canonical)});
const fragments = {script_json(fragments)};
let fragment = location.hash.slice(1);
try {{ fragment = decodeURIComponent(fragment); }} catch {{}}
target.search = location.search;
target.hash = Object.hasOwn(fragments, fragment) ? fragments[fragment] : location.hash;
location.replace(target.href);
</script>
</head>
<body>
<h1>Articolul are o adresă nouă</h1>
<p><a href="{escape(canonical, quote=True)}">Continuă către articol</a>.</p>
</body>
</html>
'''
        (destination/'index.html').write_text(html, encoding='utf-8')
        (destination/'index.md').write_text(
            '# Articolul are o adresă nouă\n\n'
            f'[Citește articolul]({canonical}) sau '
            f'[deschide versiunea Markdown]({canonical}index.md).\n', encoding='utf-8')
    return len(PAGE_REDIRECTS)
