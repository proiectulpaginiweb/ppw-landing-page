#!/usr/bin/env python3
"""Generate discovery files from the same HTML visitors read (standard library only)."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import re
from seo import update_metadata

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

# Content is taken from visible headings, prose, lists and every journey panel.
lines = ['# '+NAME, '', '> '+description, '', 'Site oficial: '+SITE, '', 'Limba: română.', '']
IGNORE = {'script','style','svg','form','button'}
def markdown(node):
    if node.tag in IGNORE or node.attrs.get('aria-hidden') == 'true':
        return
    if node.tag == 'li' and any(True for _ in node.all(lambda n: 'step-icon' in n.attrs.get('class', '').split())):
        number = node.first(lambda n: 'step-icon' in n.attrs.get('class', '').split()).text()
        title = node.first(lambda n: n.tag == 'strong').text()
        description = node.first(lambda n: n.tag == 'span' and 'step-icon' not in n.attrs.get('class', '').split()).text()
        lines.extend([f'{int(number)}. **{title}** — {description}', ''])
        return
    if node.tag in {'h1','h2','h3','p','li','summary'}:
        text = node.text().replace('＋','').replace('✳','').strip()
        if text:
            prefix = '#' * int(node.tag[1]) + ' ' if node.tag in {'h1','h2','h3'} else '- ' if node.tag == 'li' else '### ' if node.tag == 'summary' else ''
            lines.extend([prefix+text,''])
        return
    if 'journey-deliverable' in node.attrs.get('class','').split():
        lines.extend(['**Ce obții:** '+node.first(lambda n:n.tag=='strong').text(),''])
        return
    for child in node.children:
        if isinstance(child, Node): markdown(child)
markdown(main)
lines.extend(['## Contact','','Folosește formularul de pe '+SITE+'#contact pentru a trimite numele, adresa de e-mail, interesul și descrierea proiectului.',''])
(ROOT/'index.md').write_text('\n'.join(lines), encoding='utf-8')

def inline_markdown(node, base_url=None):
    if isinstance(node, str):
        return node
    if base_url and (node.tag in IGNORE or node.attrs.get('aria-hidden') == 'true'):
        return ''
    content = ''.join(inline_markdown(c, base_url) for c in node.children)
    if node.tag == 'a':
        href = urljoin(base_url, node.attrs['href']) if base_url else node.attrs['href']
        return '[' + content.strip() + '](' + href + ')'
    if node.tag == 'code':
        return '`' + content + '`'
    return content

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
    page_lines = ['Pagina: ' + page_url, '']
    block_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'dl'}

    def page_markdown(node):
        if node.tag in IGNORE or node.attrs.get('aria-hidden') == 'true':
            return
        has_blocks = any(True for _ in node.all(lambda n: n.tag in block_tags))
        if node.tag in block_tags - {'ul', 'ol', 'dl'} or (node.tag in {'li', 'a', 'dt', 'dd', 'figcaption', 'summary'} and not has_blocks):
            content = re.sub(r'\s+', ' ', inline_markdown(node, page_url)).strip()
            if content:
                prefix = '#' * int(node.tag[1]) + ' ' if node.tag.startswith('h') else '- ' if node.tag == 'li' else ''
                page_lines.extend([prefix + content, ''])
            return
        for child in node.children:
            if isinstance(child, Node):
                page_markdown(child)

    page_markdown(page_main)
    page_content = '\n'.join(page_lines).rstrip() + '\n'
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
    for child in article_body.children:
        if not isinstance(child, Node):
            continue
        if child.tag in {'h2', 'h3'}:
            article_lines.extend(['#' * int(child.tag[1]) + ' ' + child.text(), ''])
        elif child.tag == 'p':
            article_lines.extend([re.sub(r'\s+', ' ', inline_markdown(child)).strip(), ''])
        elif child.tag == 'pre':
            code = child.first(lambda n: n.tag == 'code')
            language = code.attrs.get('class', '').partition('language-')[2]
            article_lines.extend(['```' + language, ''.join(code.children), '```', ''])
        elif child.tag == 'figure':
            image = child.first(lambda n: n.tag == 'img')
            caption = child.first(lambda n: n.tag == 'figcaption')
            image_url = urljoin(article_url, image.attrs['src'])
            article_lines.extend([f"![{image.attrs['alt']}]({image_url})", '', inline_markdown(caption).strip(), ''])
        elif child.tag == 'blockquote':
            article_lines.extend(['> ' + child.text(), ''])
        elif child.tag == 'nav' and 'post-related' in child.attrs.get('class', '').split():
            for item in child.all(lambda n: n.tag in {'p', 'a'}):
                article_lines.extend([re.sub(r'\s+', ' ', inline_markdown(item, article_url)).strip(), ''])
        elif child.tag in {'ul', 'ol'}:
            for i, item in enumerate((n for n in child.children if isinstance(n, Node) and n.tag == 'li'), 1):
                prefix = f'{i}. ' if child.tag == 'ol' else '- '
                article_lines.extend([prefix + re.sub(r'\s+', ' ', inline_markdown(item)).strip(), ''])
        elif 'post-facts' in child.attrs.get('class', '').split():
            for fact in child.all(lambda n: n.tag == 'div'):
                article_lines.extend(['### ' + fact.first(lambda n: n.tag == 'strong').text(), ''])
                paragraph = fact.first(lambda n: n.tag == 'p')
                article_lines.extend([re.sub(r'\s+', ' ', inline_markdown(paragraph)).strip(), ''])
    article_markdown = '\n'.join(article_lines).rstrip() + '\n'
    article_path.with_suffix('.md').write_text(article_markdown, encoding='utf-8')
    articles.append({
        'title': article_title, 'date': article_date, 'description': article_description,
        'language': article_language, 'url': article_url, 'markdown': article_markdown,
    })

article_links = []
for article in articles:
    article_links.append(f"- [{article['title']}]({article['url']}): {article['description']}")
    markdown_label = 'Article in Markdown' if article['language'].split('-')[0].lower() == 'en' else 'Articolul în Markdown'
    article_links.append(f"- [{markdown_label}]({article['url'].rstrip('/')}/index.md): {article['title']}")
article_links = '\n'.join(article_links)
page_links = '\n'.join(
    f"- [{page['title']}]({page['url']}): {page['description']}\n"
    f"- [Pagina în Markdown]({page['url'].rstrip('/')}/index.md): {page['title']}"
    for page in pages
)

(ROOT/'llms.txt').write_text(f'''# {NAME}

> {description}

Site oficial: {SITE}

## Conținut

- [Prezentare completă în Markdown]({SITE}index.md): serviciile, cele patru etape ale colaborării, principiile și întrebările frecvente.
- [Conținut integral]({SITE}llms-full.txt): textul paginii principale, al paginii despre echipă, al blogului și al tuturor articolelor.
- [Pagina principală]({SITE}): versiunea HTML în română.
{page_links}
- [Blog]({SITE}blog/): articole despre tehnologie și experiențe digitale.
{article_links}
- [Servicii]({SITE}#posibilitati): agenți IA, automatizarea proceselor și experiențe digitale cu IA.
- [Parcursul colaborării]({SITE}#parcurs): descoperire, proiectare, construcție și îmbunătățire.
- [Întrebări frecvente]({SITE}#intrebari): explicații despre agenți IA, proiecte-pilot și date.
- [Contact]({SITE}#contact): formularul de contact.

Exemplul de proces pentru relația cu clienții este ilustrativ. Pagina nu publică prețuri, garanții de performanță sau mărturii ale clienților.
''', encoding='utf-8')
# Full content is regenerated from the visible pages.
(ROOT/'llms-full.txt').write_text('\n\n---\n\n'.join([(ROOT/'index.md').read_text(encoding='utf-8').rstrip(), *(page['markdown'].rstrip() for page in pages), *(article['markdown'].rstrip() for article in articles)]) + '\n', encoding='utf-8')
(ROOT/'.nojekyll').touch()
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+SITE+'sitemap.xml\n', encoding='utf-8')
sitemap_urls = list(dict.fromkeys([SITE, *(page['url'] for page in pages), SITE+'blog/', *(article['url'] for article in articles)]))
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join('  <url><loc>'+escape(url)+'</loc></url>\n' for url in sitemap_urls) + '</urlset>\n', encoding='utf-8')
print('Au fost generate metadatele canonice, JSON-LD, robots.txt, sitemap.xml, llms.txt și copiile Markdown din paginile HTML.')
