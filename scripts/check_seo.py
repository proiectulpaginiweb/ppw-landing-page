#!/usr/bin/env python3
"""Validate the static site's SEO contracts without third-party dependencies."""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.proiectulpaginiweb.ro/'
NAME = 'Proiectul Pagini Web'
HOSTS = {'www.proiectulpaginiweb.ro', 'proiectulpaginiweb.ro'}
PAGE_TYPES = {'WebPage', 'AboutPage', 'ProfilePage', 'CollectionPage', 'ContactPage'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def walk(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.walk()

    def text(self):
        def collect(node):
            if isinstance(node, str):
                return node
            if node.attrs.get('aria-hidden') == 'true' or node.tag in {'script', 'style', 'svg'}:
                return ''
            if node.tag == 'br':
                return ' '
            return ''.join(collect(child) for child in node.children)
        return re.sub(r'\s+', ' ', collect(self)).strip()

    def raw_text(self):
        return ''.join(child.raw_text() if isinstance(child, Node) else child for child in self.children)


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node('')
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def types(entity):
    value = entity.get('@type', [])
    return {value} if isinstance(value, str) else set(value) if isinstance(value, list) else set()


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def expected_url(path):
    parent = path.relative_to(ROOT).parent.as_posix()
    return SITE if parent == '.' else SITE + parent + '/'


class Audit:
    def __init__(self):
        self.errors = []
        self.pages = {}
        self.titles = defaultdict(list)
        self.descriptions = defaultdict(list)

    def require(self, condition, path, message):
        if not condition:
            label = str(path.relative_to(ROOT)) if isinstance(path, Path) else str(path)
            self.errors.append(f'{label}: {message}')
        return condition

    def load(self, path):
        if path in self.pages:
            return self.pages[path]
        try:
            source = path.read_text(encoding='utf-8', errors='strict')
        except (OSError, UnicodeError) as error:
            self.require(False, path, f'cannot read UTF-8 HTML ({error})')
            return None
        document = Document(source).root
        self.pages[path] = document
        return document

    def one(self, nodes, path, label):
        self.require(len(nodes) == 1, path, f'expected one {label}, found {len(nodes)}')
        return nodes[0] if nodes else None

    def meta(self, nodes, attribute, key, path):
        matches = [node for node in nodes if node.tag == 'meta'
                   and node.attrs.get(attribute, '').lower() == key]
        node = self.one(matches, path, key + ' meta tag')
        value = node.attrs.get('content', '').strip() if node else ''
        self.require(bool(value), path, key + ' must not be empty')
        return value

    def local_ref(self, path, reference, label):
        url = urlsplit(urljoin(expected_url(path), reference))
        if url.scheme not in {'http', 'https'} or url.hostname not in HOSTS:
            return
        target = (ROOT / unquote(url.path).lstrip('/')).resolve()
        if not target.is_relative_to(ROOT):
            self.require(False, path, f'{label} leaves site root: {reference}')
            return
        if target.is_dir():
            target /= 'index.html'
        if not self.require(target.is_file(), path, f'missing {label}: {reference}'):
            return
        if url.fragment and target.suffix == '.html':
            document = self.load(target)
            if document:
                ids = {node.attrs.get('id') for node in document.walk()}
                self.require(unquote(url.fragment) in ids, path, f'missing anchor: {reference}')

    def linked_resources(self, path, nodes):
        for node in nodes:
            for attribute in ('href', 'src', 'action', 'poster'):
                reference = node.attrs.get(attribute)
                if not reference:
                    continue
                self.local_ref(path, reference, attribute + ' target')
                is_resource = attribute != 'href' or node.tag == 'link'
                if is_resource:
                    self.require(not reference.startswith(('http://', '//')), path,
                                 f'insecure resource URL: {reference}')
            for candidate in node.attrs.get('srcset', '').split(','):
                if candidate.strip():
                    reference = candidate.strip().split()[0]
                    self.local_ref(path, reference, 'srcset image')
                    self.require(not reference.startswith(('http://', '//')), path,
                                 f'insecure srcset URL: {reference}')
            if node.tag == 'img':
                # An explicitly empty alt attribute marks an intentionally decorative image.
                self.require('alt' in node.attrs, path, 'image is missing alt text (use alt="" for decoration)')
                for dimension in ('width', 'height'):
                    value = node.attrs.get(dimension, '')
                    self.require(value.isdigit() and int(value) > 0, path,
                                 f'image needs a positive {dimension}: {node.attrs.get("src", "")}')

    def breadcrumbs(self, path, nodes, entities, canonical):
        graphs = [entity for entity in entities if 'BreadcrumbList' in types(entity)]
        breadcrumb = self.one(graphs, path, 'BreadcrumbList')
        navs = [node for node in nodes if node.tag == 'nav'
                and ('breadcrumb' in node.attrs.get('class', '')
                     or node.attrs.get('aria-label', '').casefold() == 'fir de navigare')]
        nav = self.one(navs, path, 'visible breadcrumb navigation')
        if not breadcrumb or not nav:
            return
        items = breadcrumb.get('itemListElement', [])
        if not self.require(isinstance(items, list) and len(items) >= 2, path,
                            'BreadcrumbList needs at least two ListItems'):
            return
        visible = [node for node in nav.walk()
                   if node.tag == 'a' or node.attrs.get('aria-current') == 'page']
        self.require(len(items) == len(visible), path, 'breadcrumb markup and visible trail differ in length')
        for position, item in enumerate(items, 1):
            if not self.require(isinstance(item, dict), path, 'breadcrumb item is not an object'):
                continue
            self.require('ListItem' in types(item), path, 'breadcrumb item must have type ListItem')
            self.require(item.get('position') == position, path, 'breadcrumb positions must be consecutive from 1')
            self.require(bool(item.get('name')), path, 'breadcrumb name is missing')
            target = item.get('item', canonical if position == len(items) else '')
            if isinstance(target, dict):
                target = target.get('@id', '')
            self.require(bool(target), path, 'breadcrumb URL is missing')
            if position <= len(visible):
                node = visible[position - 1]
                self.require(item.get('name') == node.text(), path, 'breadcrumb name differs from visible text')
                expected = urljoin(canonical, node.attrs.get('href', canonical))
                self.require(target == expected, path, 'breadcrumb URL differs from visible navigation')

    def article(self, path, nodes, entities, ids, canonical):
        articles = [entity for entity in entities if 'BlogPosting' in types(entity)]
        article = self.one(articles, path, 'BlogPosting')
        h1 = next((node for node in nodes if node.tag == 'h1'), None)
        post = next((node for node in nodes if node.tag == 'article'
                     and 'post' in node.attrs.get('class', '').split()), None)
        if not article or not h1 or not post:
            self.require(bool(post), path, 'article content container is missing')
            return
        self.require(article.get('headline') == h1.text(), path, 'BlogPosting headline differs from H1')
        self.require(article.get('url') == canonical, path, 'BlogPosting URL differs from canonical')
        parsed_dates = {}
        for property_name in ('datePublished', 'dateModified'):
            value = article.get(property_name, '')
            try:
                parsed_dates[property_name] = datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            except (TypeError, ValueError, AttributeError):
                self.require(False, path, f'{property_name} is not a valid ISO date')
        if len(parsed_dates) == 2:
            self.require(parsed_dates['dateModified'] >= parsed_dates['datePublished'], path,
                         'dateModified precedes datePublished')
            modified = post.attrs.get('data-date-modified', '')
            self.require(modified == parsed_dates['dateModified'].isoformat(), path,
                         'dateModified differs from authored data-date-modified')
            visible_times = [node.attrs.get('datetime') for node in post.walk()
                             if node.tag == 'time' and node.text()]
            self.require(parsed_dates['datePublished'].isoformat() in visible_times, path,
                         'datePublished differs from visible publication time')
            if parsed_dates['dateModified'] != parsed_dates['datePublished']:
                self.require(parsed_dates['dateModified'].isoformat() in visible_times, path,
                             'changed dateModified must also be visible on the page')
        authors = article.get('author', [])
        authors = authors if isinstance(authors, list) else [authors]
        self.require(bool(authors), path, 'BlogPosting author is missing')
        for author in authors:
            if not isinstance(author, dict):
                self.require(False, path, 'BlogPosting author must be an Organization object')
                continue
            author = ids.get(author.get('@id'), author)
            self.require('Organization' in types(author) and author.get('name') == NAME
                         and author.get('url') == SITE, path, 'author must identify the visible PPW Organization')
        author_links = [node for node in post.walk() if node.tag == 'a'
                        and 'author' in node.attrs.get('rel', '').split()]
        self.require(any(node.text() == NAME and urljoin(canonical, node.attrs.get('href', '')) == SITE
                         for node in author_links), path, 'visible PPW author link is missing')

    def page(self, path):
        document = self.load(path)
        if document is None:
            return
        nodes = list(document.walk())
        canonical = expected_url(path)
        html = self.one([node for node in nodes if node.tag == 'html'], path, 'html element')
        if html:
            self.require(html.attrs.get('lang', '').lower().split('-')[0] == 'ro', path, 'HTML language must be Romanian')
        charset = self.one([node for node in nodes if node.tag == 'meta' and 'charset' in node.attrs], path,
                           'charset declaration')
        if charset:
            self.require(charset.attrs['charset'].lower() == 'utf-8', path, 'charset must be UTF-8')
        title_node = self.one([node for node in nodes if node.tag == 'title'], path, 'title')
        title = title_node.text() if title_node else ''
        self.require(bool(title), path, 'title is empty')
        self.titles[title.casefold()].append(path)
        description = self.meta(nodes, 'name', 'description', path)
        self.descriptions[description.casefold()].append(path)
        self.one([node for node in nodes if node.tag == 'h1'], path, 'H1')
        links = [node for node in nodes if node.tag == 'link']
        canonical_node = self.one([node for node in links if 'canonical' in node.attrs.get('rel', '').split()],
                                  path, 'canonical link')
        if canonical_node:
            self.require(canonical_node.attrs.get('href') == canonical, path, f'canonical must be {canonical}')
        robots = self.meta(nodes, 'name', 'robots', path).lower()
        tokens = set(re.split(r'[\s,]+', robots))
        self.require('index' in tokens and not tokens.intersection({'noindex', 'none'}), path,
                     'indexable page must allow indexing')
        viewport = self.meta(nodes, 'name', 'viewport', path).replace(' ', '').lower()
        self.require('width=device-width' in viewport, path, 'viewport needs width=device-width')
        for property_name in ('og:title', 'og:description', 'og:type', 'og:locale', 'og:site_name', 'og:url'):
            value = self.meta(nodes, 'property', property_name, path)
            if property_name == 'og:url':
                self.require(value == canonical, path, 'og:url differs from canonical')
            elif property_name == 'og:site_name':
                self.require(value == NAME, path, 'og:site_name differs from site identity')
        font_links = [node for node in links if 'stylesheet' in node.attrs.get('rel', '').split()
                      and urlsplit(urljoin(canonical, node.attrs.get('href', ''))).path == '/styles.min.css']
        self.require(len(font_links) == 1, path, 'one local shared stylesheet with font faces is required')
        self.require(not any(urlsplit(node.attrs.get('href', '')).hostname in
                             {'fonts.googleapis.com', 'fonts.gstatic.com'} for node in links), path,
                     'font loading must not depend on third-party font connections')
        for filename in ('dm-sans-latin.woff2', 'manrope-latin.woff2'):
            preloads = [node for node in links if 'preload' in node.attrs.get('rel', '').split()
                        and urlsplit(node.attrs.get('href', '')).path.endswith('/'+filename)]
            self.require(len(preloads) == 1 and preloads[0].attrs.get('as') == 'font'
                         and preloads[0].attrs.get('type') == 'font/woff2'
                         and 'crossorigin' in preloads[0].attrs, path,
                         f'{filename} needs one cross-origin-compatible WOFF2 font preload')
        identifiers = [node.attrs['id'] for node in nodes if 'id' in node.attrs]
        self.require(len(identifiers) == len(set(identifiers)), path, 'duplicate HTML IDs')
        self.linked_resources(path, nodes)
        entities = []
        json_scripts = [node for node in nodes if node.tag == 'script'
                        and node.attrs.get('type') == 'application/ld+json']
        self.require(bool(json_scripts), path, 'JSON-LD is missing')
        for script in json_scripts:
            try:
                value = json.loads(script.raw_text())
                entities.extend(objects(value))
            except json.JSONDecodeError as error:
                self.require(False, path, f'invalid JSON-LD: {error.msg}')
        ids = {entity['@id']: entity for entity in entities if '@id' in entity and len(entity) > 1}
        page_entities = [entity for entity in entities if types(entity).intersection(PAGE_TYPES)
                         and (entity.get('url') == canonical or entity.get('@id', '').startswith(canonical + '#'))]
        self.require(bool(page_entities), path, 'JSON-LD needs a WebPage entity for the canonical page')
        if path != ROOT / 'index.html':
            self.breadcrumbs(path, nodes, entities, canonical)
        if path.parent.parent == ROOT / 'blog':
            self.article(path, nodes, entities, ids, canonical)
        if path == ROOT / 'echipa/index.html':
            profiles = [entity for entity in entities if 'ProfilePage' in types(entity)]
            profile = self.one(profiles, path, 'ProfilePage')
            person = profile.get('mainEntity', {}) if profile else {}
            if isinstance(person, dict):
                person = ids.get(person.get('@id'), person)
            if self.require(isinstance(person, dict) and 'Person' in types(person), path,
                            'ProfilePage mainEntity must identify a Person'):
                self.require(person.get('name') == 'Sîrbu Nicolae-Cezar', path, 'profile Person name differs from visible identity')
                self.require({'https://www.linkedin.com/in/sarbull/', 'https://github.com/sarbull'}
                             .issubset(set(person.get('sameAs', []))), path, 'profile must retain its verified sameAs sources')

    def sitemap(self, paths):
        path = ROOT / 'sitemap.xml'
        try:
            tree = ET.fromstring(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, ET.ParseError) as error:
            self.require(False, path, f'invalid UTF-8 sitemap ({error})')
            return
        namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locations = [node.text for node in tree.findall('s:url/s:loc', namespace)]
        expected = {expected_url(page) for page in paths}
        self.require(set(locations) == expected and len(locations) == len(expected), path,
                     'sitemap must contain each canonical HTML page exactly once, without Markdown or index.html aliases')
        for modified in tree.findall('s:url/s:lastmod', namespace):
            try:
                datetime.fromisoformat((modified.text or '').replace('Z', '+00:00'))
            except ValueError:
                self.require(False, path, 'lastmod is not a valid ISO date')
        robots = ROOT / 'robots.txt'
        try:
            source = robots.read_text(encoding='utf-8')
            self.require('Sitemap: ' + SITE + 'sitemap.xml' in source, robots, 'canonical sitemap declaration is missing')
            self.require(not re.search(r'^\s*Disallow:\s*/\s*$', source, flags=re.M | re.I), robots,
                         'robots.txt blocks the whole site')
        except (OSError, UnicodeError) as error:
            self.require(False, robots, f'cannot read UTF-8 robots.txt ({error})')

    def css(self):
        for path in sorted(ROOT.rglob('*.css')):
            if any(part in {'.git', 'node_modules'} for part in path.relative_to(ROOT).parts):
                continue
            source = path.read_text(encoding='utf-8')
            source = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
            self.require(not re.search(r'@import\b', source, flags=re.I), path,
                         'CSS @import delays resource discovery; use HTML stylesheet links')
            self.require(not re.search(r'url\(\s*[\"\']?(?:http://|//)', source, flags=re.I), path,
                         'CSS contains an insecure resource URL')

        font_css = ROOT/'fonts.css'
        try:
            source = font_css.read_text(encoding='utf-8')
            faces = re.findall(r'@font-face\s*\{([^}]+)\}', source, flags=re.I)
            self.require(len(faces) == 4, font_css, 'expected Latin and Latin-ext variable faces for both fonts')
            for family, weights in (('DM Sans', '400 700'), ('Manrope', '400 800')):
                matching = [face for face in faces if re.search(
                    r'font-family:\s*[\"\']'+re.escape(family)+r'[\"\']', face)]
                self.require(len(matching) == 2, font_css, f'{family} needs Latin and Latin-ext faces')
                for face in matching:
                    self.require(bool(re.search(r'font-weight:\s*'+weights+r'\s*;', face)), font_css,
                                 f'{family} must preserve the authored variable weight range')
                    self.require(bool(re.search(r'font-display:\s*swap\s*;', face)), font_css,
                                 'font-display: swap keeps text visible while fonts load')
            for reference in re.findall(r'url\([\"\']?([^\)\"\']+)', source):
                font = (ROOT/unquote(urlsplit(reference).path)).resolve()
                self.require(font.is_relative_to(ROOT) and font.suffix == '.woff2' and
                             font.is_file() and font.read_bytes()[:4] == b'wOF2', font_css,
                             f'missing or invalid local WOFF2 font: {reference}')
            for family in ('dm-sans', 'manrope'):
                license_path = ROOT/'assets/fonts'/(family+'-OFL.txt')
                self.require(license_path.is_file() and 'SIL Open Font License' in
                             license_path.read_text(encoding='utf-8'), font_css,
                             f'{family} font license must accompany the font files')
        except (OSError, UnicodeError) as error:
            self.require(False, font_css, f'cannot validate local fonts ({error})')

    def run(self):
        paths = [ROOT / 'index.html', ROOT / 'blog/index.html', ROOT / 'echipa/index.html',
                 *sorted((ROOT / 'blog').glob('*/index.html'))]
        for path in paths:
            self.page(path)
        for label, values in (('title', self.titles), ('description', self.descriptions)):
            for value, duplicates in values.items():
                self.require(not value or len(duplicates) == 1, 'site',
                             f'duplicate {label}: ' + ', '.join(str(path.relative_to(ROOT)) for path in duplicates))
        self.sitemap(paths)
        self.css()
        if self.errors:
            print(f'SEO validation failed ({len(self.errors)} issues):')
            for error in self.errors:
                print('- ' + error)
            return 1
        print(f'SEO checks passed for {len(paths)} pages: metadata, structured data, canonical URLs, links, images and sitemap.')
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='static site directory to validate')
    ROOT = parser.parse_args().root.resolve()
    sys.exit(Audit().run())
