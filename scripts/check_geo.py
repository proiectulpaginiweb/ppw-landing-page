#!/usr/bin/env python3
"""Check that public facts, sources and summaries survive every content format."""
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import argparse
import json
import re
import sys
import unicodedata

from check_seo import Document, objects, types


ROOT = Path(__file__).resolve().parent.parent
PERSON_SOURCES = {'https://www.linkedin.com/in/sarbull', 'https://github.com/sarbull'}
LINK = re.compile(r'!?\[([^\]]*)\]\(([^\s)]+)(?:\s+["\'][^)]*["\'])?\)')


def text_value(source):
    """Compare prose while allowing normal Markdown links and emphasis."""
    source = LINK.sub(lambda match: match[1], source)
    source = source.replace('\\|', '|').replace('**', '').replace('*', '').replace('`', '')
    return re.sub(r'\s+', ' ', source).strip()


def links(source):
    # Code samples may legitimately contain Markdown-looking syntax as data.
    source = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', source, flags=re.M | re.S)
    return [match[2] for match in LINK.finditer(source)]


def has_class(node, name):
    return name in node.attrs.get('class', '').split()


class Audit:
    def __init__(self, root):
        self.root = root
        self.errors = []
        self.documents = {}

    def require(self, condition, path, message):
        if not condition:
            label = str(path.relative_to(self.root)) if isinstance(path, Path) else str(path)
            self.errors.append(f'{label}: {message}')
        return condition

    def read(self, path):
        try:
            source = path.read_text(encoding='utf-8', errors='strict')
        except (OSError, UnicodeError) as error:
            self.require(False, path, f'cannot read UTF-8 text ({error})')
            return ''
        self.require(source == unicodedata.normalize('NFC', source), path, 'text is not NFC-normalized')
        self.require('\ufffd' not in source, path, 'text contains a Unicode replacement character')
        return source

    def document(self, path):
        if path not in self.documents:
            self.documents[path] = Document(self.read(path)).root
        return self.documents[path]

    def entities(self, path):
        entities = []
        for node in self.document(path).walk():
            if node.tag == 'script' and node.attrs.get('type') == 'application/ld+json':
                try:
                    entities.extend(objects(json.loads(node.raw_text())))
                except json.JSONDecodeError as error:
                    self.require(False, path, f'invalid JSON-LD ({error.msg})')
        return entities

    def canonical(self, path):
        node = next((node for node in self.document(path).walk() if node.tag == 'link'
                     and 'canonical' in node.attrs.get('rel', '').split()), None)
        return node.attrs.get('href', '') if node else ''

    def markdown(self, path):
        source = self.read(path)
        for target in links(source):
            parsed = urlsplit(target)
            valid = parsed.scheme == 'https' and bool(parsed.netloc)
            valid = valid or (parsed.scheme == 'mailto' and '@' in parsed.path)
            self.require(valid, path, f'Markdown target must be an absolute HTTPS URL or email: {target}')
        return source

    def article(self, path, markdown, aggregate):
        document = self.document(path)
        nodes = list(document.walk())
        summary = [node for node in nodes if has_class(node, 'post-summary')]
        if not self.require(len(summary) == 1, path, 'expected one visible .post-summary'):
            return
        summary = summary[0]
        self.require(summary.attrs.get('aria-hidden') != 'true' and 'hidden' not in summary.attrs,
                     path, 'article summary must be visible')
        heading = next((node for node in summary.walk() if node.tag in {'h2', 'h3'}), None)
        self.require(heading is not None and bool(heading.text()), path, 'summary heading is missing')
        items = [node for node in summary.walk() if node.tag == 'li']
        self.require(len(items) == 3, path, 'summary must retain its three editorial takeaways')
        for node in ([heading] if heading else []) + items:
            expected = text_value(node.text())
            for name, content in (('Markdown copy', markdown), ('llms-full.txt', aggregate)):
                self.require(bool(expected) and expected in text_value(content), path,
                             f'summary text is missing from {name}: {node.text()}')

        canonical = self.canonical(path)
        body = next((node for node in nodes if has_class(node, 'post-body')), None)
        if not self.require(body is not None, path, 'article body is missing'):
            return
        host = urlsplit(canonical).hostname
        site_hosts = {host, host.removeprefix('www.')} if host else set()
        sources = set()
        for node in body.walk():
            if node.tag != 'a' or node.attrs.get('aria-hidden') == 'true' or not node.text():
                continue
            target = urljoin(canonical, node.attrs.get('href', ''))
            parsed = urlsplit(target)
            if parsed.scheme in {'http', 'https'} and parsed.hostname not in site_hosts:
                sources.add(target)
        markdown_targets = set(links(markdown))
        aggregate_targets = set(links(aggregate))
        articles = [entity for entity in self.entities(path) if 'BlogPosting' in types(entity)]
        citation_targets = set()
        for article in articles:
            citations = article.get('citation', [])
            citations = citations if isinstance(citations, list) else [citations]
            for citation in citations:
                if isinstance(citation, str):
                    citation_targets.add(citation)
                elif isinstance(citation, dict):
                    citation_targets.add(citation.get('url', citation.get('@id', '')))
        for target in sorted(sources):
            self.require(target in markdown_targets, path, f'visible source is missing from Markdown: {target}')
            self.require(target in aggregate_targets, path, f'visible source is missing from llms-full.txt: {target}')
            self.require(target in citation_targets, path, f'visible source is missing from BlogPosting.citation: {target}')
        self.require(citation_targets == sources, path,
                     'BlogPosting.citation must match the visible external article sources')

    def identity(self, paths, home_markdown, aggregate):
        home = self.root/'index.html'
        home_document = self.document(home)
        nodes = list(home_document.walk())
        definition = next((node for node in nodes if node.attrs.get('id') == 'despre-ppw'), None)
        if self.require(definition is not None, home, 'visible #despre-ppw definition is missing'):
            paragraphs = [definition] if definition.tag == 'p' else [node for node in definition.walk() if node.tag == 'p']
            self.require(bool(paragraphs), home, 'PPW definition has no prose')
            for paragraph in paragraphs:
                expected = text_value(paragraph.text())
                for name, content in (('Markdown copy', home_markdown), ('llms-full.txt', aggregate)):
                    self.require(bool(expected) and expected in text_value(content), home,
                                 f'PPW definition is missing from {name}')
        organizations = [entity for entity in self.entities(home) if 'Organization' in types(entity)
                         and entity.get('url') == self.canonical(home)]
        named = [entity for entity in organizations if entity.get('name') == 'Proiectul Pagini Web']
        self.require(bool(named), home, 'Organization must identify Proiectul Pagini Web by its full name')

        ids = {node.attrs['id'] for node in nodes if 'id' in node.attrs}
        services = [entity for entity in self.entities(home) if 'Service' in types(entity)]
        visible_services = [node for node in nodes if node.tag == 'article' and has_class(node, 'service')]
        self.require(len(services) == len(visible_services) > 0, home,
                     'structured services must correspond to the visible service list')
        service_urls = []
        for service in services:
            target = service.get('url', '')
            parsed = urlsplit(target)
            self.require(target.split('#', 1)[0] == self.canonical(home)
                         and bool(parsed.fragment) and parsed.fragment in ids, home,
                         f'Service URL must target an existing canonical homepage anchor: {target}')
            service_urls.append(target)
        self.require(len(service_urls) == len(set(service_urls)), home,
                     'each Service needs its own stable anchor URL')

        profile_sources = set()
        for path in paths:
            for entity in self.entities(path):
                same_as = entity.get('sameAs', [])
                same_as = [same_as] if isinstance(same_as, str) else same_as
                if not isinstance(same_as, list):
                    continue
                same_as = {target.rstrip('/') for target in same_as if isinstance(target, str)}
                if 'Organization' in types(entity):
                    self.require(not same_as.intersection(PERSON_SOURCES), path,
                                 'personal LinkedIn/GitHub profiles must not identify the Organization')
                if 'Person' in types(entity) and entity.get('name') == 'Sîrbu Nicolae-Cezar':
                    profile_sources.update(same_as)
        self.require(PERSON_SOURCES.issubset(profile_sources), self.root/'echipa/index.html',
                     'Person must retain both verified personal source profiles')

    def run(self):
        paths = [self.root/'index.html', self.root/'blog/index.html', self.root/'echipa/index.html',
                 *sorted((self.root/'blog').glob('*/index.html'))]
        aggregate = self.markdown(self.root/'llms-full.txt')
        directory = self.markdown(self.root/'llms.txt')
        copies = {path: self.markdown(path.with_suffix('.md')) for path in paths}
        for path in paths:
            if path.parent.parent == self.root/'blog':
                self.article(path, copies[path], aggregate)
        self.identity(paths, copies[self.root/'index.html'], aggregate)
        directory_targets = Counter(target for target in links(directory) if not urlsplit(target).fragment)
        for path in paths:
            canonical = self.canonical(path)
            self.require(bool(canonical) and directory_targets[canonical] == 1, self.root/'llms.txt',
                         f'canonical HTML page must appear once in the directory: {canonical or path.name}')
        if self.errors:
            print(f'GEO content checks failed ({len(self.errors)} issues):')
            for error in self.errors:
                print('- '+error)
            return 1
        print(f'GEO content checks passed for {len(paths)} pages: summaries, sources, Markdown and entity consistency.')
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='static site directory to validate')
    sys.exit(Audit(parser.parse_args().root.resolve()).run())
