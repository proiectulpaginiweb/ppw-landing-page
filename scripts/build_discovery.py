#!/usr/bin/env python3
"""Generate discovery files from the same HTML visitors read (standard library only)."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import re
from seo import update_metadata
from markdown_content import inline_markdown, render_markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.proiectulpaginiweb.ro/'
NAME = 'Proiectul Pagini Web'

class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def text(self):
        def content(node):
            if isinstance(node, str):
                return node
            if node.attrs.get('aria-hidden') == 'true':
                return ''
            return ''.join(content(child) for child in node.children)
        return re.sub(r'\s+', ' ', content(self)).strip()
    def all(self, predicate):
        for c in self.children:
            if isinstance(c, Node):
                if predicate(c):
                    yield c
                yield from c.all(predicate)
    def first(self, predicate):
        return next(self.all(predicate))

class Document(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.stack[-1].children.append(' ')
            return
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in self.VOID:
            self.stack.append(n)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                return
    def handle_data(self, text):
        self.stack[-1].children.append(text)

update_metadata(ROOT, SITE, NAME, Document)
html_path = ROOT / 'index.html'
source = html_path.read_text(encoding='utf-8')
doc = Document(source).root
main = doc.first(lambda n: n.tag == 'main')
description = doc.first(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'description').attrs['content']

# All readable exports use the same recursive renderer as the visible HTML.
lines = ['# '+NAME, '', '> '+description, '', 'Site oficial: '+SITE, '', 'Limba: română.', '',
         render_markdown(main, SITE).rstrip(), '', '## Contact', '',
         'Folosește [formularul de contact]('+SITE+'#contact) pentru a trimite numele, adresa de e-mail, interesul și descrierea proiectului.', '']
(ROOT/'index.md').write_text('\n'.join(lines), encoding='utf-8')

# Ordinary pages keep their own metadata and do not use blog publication fields.
pages = []
for page_path in (ROOT/'echipa/index.html', ROOT/'blog/index.html'):
    if not page_path.exists():
        continue
    page = Document(page_path.read_text(encoding='utf-8')).root
    page_main = page.first(lambda n: n.tag == 'main')
    page_url = page.first(lambda n: n.tag == 'link' and 'canonical' in n.attrs.get('rel', '').split()).attrs['href']
    page_title = page.first(lambda n: n.tag == 'title').text()
    page_description = page.first(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'description').attrs['content']
    page_content = 'Pagina: ' + page_url + '\n\n' + render_markdown(page_main, page_url)
    page_path.with_suffix('.md').write_text(page_content, encoding='utf-8')
    pages.append({'title': page_title, 'description': page_description, 'url': page_url, 'markdown': page_content})

# Keep a readable copy of every article in sync with its visible HTML.
articles = []
for article_path in sorted((ROOT/'blog').glob('*/index.html')):
    article = Document(article_path.read_text(encoding='utf-8')).root
    article_main = article.first(lambda n: n.tag == 'article' and 'post' in n.attrs.get('class', '').split())
    article_body = article_main.first(lambda n: 'post-body' in n.attrs.get('class', '').split())
    article_title = article_main.first(lambda n: n.tag == 'h1').text()
    article_lead = article_main.first(lambda n: 'post-lead' in n.attrs.get('class', '').split()).text()
    article_date = article_main.first(lambda n: n.tag == 'time').attrs['datetime']
    article_modified = article_main.attrs['data-date-modified']
    article_description = article.first(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'description').attrs['content']
    article_language = article.first(lambda n: n.tag == 'html').attrs['lang']
    article_url = article.first(lambda n: n.tag == 'link' and 'canonical' in n.attrs.get('rel', '').split()).attrs['href']
    is_english = article_language.split('-')[0].lower() == 'en'
    article_lines = [
        '# ' + article_title, '',
        ('Published: ' if is_english else 'Publicat: ') + article_date, '',
        ('Article: ' if is_english else 'Articol: ') + article_url, '',
        ('Author: ' if is_english else 'Autor: ') + f'[{NAME}]({SITE})', '',
        *([('Updated: ' if is_english else 'Actualizat: ') + article_modified, ''] if article_modified != article_date else []),
        article_lead, '',
    ]
    article_lines.extend([render_markdown(article_body, article_url).rstrip(), ''])
    article_markdown = '\n'.join(article_lines).rstrip() + '\n'
    article_path.with_suffix('.md').write_text(article_markdown, encoding='utf-8')
    articles.append({
        'title': article_title, 'date': article_date, 'description': article_description,
        'language': article_language, 'url': article_url, 'markdown': article_markdown,
    })

def directory_link(label, url, description):
    return f'- [{label}]({url}): {description}'

team = next(page for page in pages if page['url'] == SITE+'echipa/')
blog = next(page for page in pages if page['url'] == SITE+'blog/')
definition = main.first(lambda n: n.attrs.get('id') == 'despre-ppw')
service_links = []
for service in main.all(lambda n: n.tag == 'article' and 'service' in n.attrs.get('class', '').split()):
    service_links.append(directory_link(service.first(lambda n: n.tag == 'h3').text(),
                         SITE+'#'+service.attrs['id'], service.first(lambda n: n.tag == 'p').text()))
article_links = []
for article in articles:
    article_links.append(directory_link(article['title'], article['url'], article['description']))
    article_links.append(directory_link('Articol în Markdown', article['url']+'index.md', article['title']))

llms_lines = [
    '# '+NAME, '', '> '+description, '', 'Site oficial: '+SITE, '',
    '## Despre PPW', '', re.sub(r'\s+', ' ', inline_markdown(definition, SITE)).strip(), '',
    directory_link('Pagina principală', SITE, 'prezentarea oficială în limba română.'),
    directory_link('Prezentare în Markdown', SITE+'index.md', 'copie a conținutului vizibil, cu surse și legături absolute.'), '',
    '## Servicii', '', *service_links, '',
    '## Echipa', '', directory_link(team['title'], team['url'], team['description']),
    directory_link('Echipa în Markdown', team['url']+'index.md', 'parcursul profesional și sursele LinkedIn/GitHub.'), '',
    '## Articole', '', directory_link(blog['title'], blog['url'], blog['description']),
    directory_link('Blog în Markdown', blog['url']+'index.md', 'lista articolelor publicate.'),
    *article_links, '', '## Colaborare și contact', '',
    directory_link('Parcursul colaborării', SITE+'#parcurs', 'descoperire, proiectare, construcție și îmbunătățire.'),
    directory_link('Întrebări frecvente', SITE+'#intrebari', 'servicii PPW, agenți IA, proiecte-pilot și date.'),
    directory_link('Contact', SITE+'#contact', 'formularul de contact pentru descrierea proiectului.'), '',
    '## Conținut integral', '',
    directory_link('Conținut integral', SITE+'llms-full.txt', 'paginile și articolele într-un singur fișier; fiecare copie indică sursa HTML.'), '',
    'Acesta este un index suplimentar. Paginile HTML sunt sursele canonice; fișierele Markdown sunt generate din același conținut vizibil.', '',
    'Exemplul de proces pentru relația cu clienții și scenariile numerice din articole sunt ilustrative. Site-ul nu publică prețuri, garanții de performanță sau mărturii ale clienților.', '',
]
(ROOT/'llms.txt').write_text('\n'.join(llms_lines), encoding='utf-8')
# Full content is regenerated from the visible pages.
(ROOT/'llms-full.txt').write_text('\n\n---\n\n'.join([(ROOT/'index.md').read_text(encoding='utf-8').rstrip(), *(page['markdown'].rstrip() for page in pages), *(article['markdown'].rstrip() for article in articles)]) + '\n', encoding='utf-8')
(ROOT/'.nojekyll').touch()
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+SITE+'sitemap.xml\n', encoding='utf-8')
sitemap_urls = list(dict.fromkeys([SITE, *(page['url'] for page in pages), SITE+'blog/', *(article['url'] for article in articles)]))
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join('  <url><loc>'+escape(url)+'</loc></url>\n' for url in sitemap_urls) + '</urlset>\n', encoding='utf-8')
print('Au fost generate metadatele canonice, JSON-LD, robots.txt, sitemap.xml, llms.txt și copiile Markdown din paginile HTML.')
