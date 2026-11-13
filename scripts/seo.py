"""Keep search metadata consistent with the site's visible, authored content."""
from hashlib import sha256
from html import escape
import json
import re
from urllib.parse import urljoin, urlsplit

FONT_URL = ('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;450;500;550;600;650;700'
            '&family=Manrope:wght@400;500;600;650;700;750;800&display=swap')


def update_metadata(root, site, name, Document):
    def has_class(node, value):
        return value in node.attrs.get('class', '').split()

    def meta(doc, key, default=''):
        node = next(doc.all(lambda n: n.tag == 'meta' and
                           (n.attrs.get('name') == key or n.attrs.get('property') == key)), None)
        return node.attrs.get('content', default) if node else default

    paths = [root/'index.html', root/'blog/index.html', root/'echipa/index.html',
             *sorted((root/'blog').glob('*/index.html'))]
    catalog = []
    for path in paths:
        source = path.read_text(encoding='utf-8')
        doc = Document(source).root
        relative = path.parent.relative_to(root).as_posix()
        url = site if relative == '.' else urljoin(site, relative + '/')
        kind = 'home' if relative == '.' else 'blog' if relative == 'blog' else 'profile' if relative == 'echipa' else 'article'
        catalog.append({'path': path, 'source': source, 'doc': doc, 'url': url, 'kind': kind,
                        'title': doc.first(lambda n: n.tag == 'title').text(),
                        'description': meta(doc, 'description'),
                        'language': doc.first(lambda n: n.tag == 'html').attrs['lang']})

    home = catalog[0]
    organization = {'@type': 'Organization', '@id': site+'#organizatie', 'name': name,
                    'url': site, 'description': home['description'], 'logo': site+'assets/ppw.png',
                    'contactPoint': {'@type': 'ContactPoint', 'contactType': 'Informații despre servicii',
                                     'url': site+'#contact', 'availableLanguage': ['ro']}}
    publisher = {'@type': 'Organization', '@id': organization['@id'], 'name': name, 'url': site,
                 'logo': {'@type': 'ImageObject', 'url': site+'assets/ppw.png'}}

    for entry in catalog:
        path, doc, url, kind = (entry[k] for k in ('path', 'doc', 'url', 'kind'))
        main = doc.first(lambda n: n.tag == 'main')
        heading = main.first(lambda n: n.tag == 'h1').text()
        webpage = {'@type': 'WebPage', '@id': url+'#pagina', 'url': url,
                   'name': entry['title'], 'description': entry['description'],
                   'inLanguage': entry['language'], 'isPartOf': {'@id': site+'#site'}}
        graph = [webpage]
        image, image_alt = site+'assets/ppw.png', 'Sigla '+name
        dates = []

        if kind == 'home':
            services = []
            for i, service in enumerate(main.all(lambda n: n.tag == 'article' and has_class(n, 'service')), 1):
                services.append({'@type': 'Service', '@id': site+'#serviciu-'+str(i),
                                 'name': service.first(lambda n: n.tag == 'h3').text(),
                                 'description': service.first(lambda n: n.tag == 'p').text(),
                                 'url': site+'#'+service.attrs.get('id', 'posibilitati'),
                                 'provider': {'@id': organization['@id']}})
            organization['hasOfferCatalog'] = {'@type': 'OfferCatalog', 'name': 'Servicii IA',
                'itemListElement': [{'@type': 'Offer', 'itemOffered': {'@id': service['@id']}} for service in services]}
            webpage['about'] = {'@id': organization['@id']}
            graph = [organization,
                     {'@type': 'WebSite', '@id': site+'#site', 'url': site, 'name': name,
                      'inLanguage': entry['language'],
                      'publisher': {'@id': organization['@id']}}, webpage, *services]

        elif kind == 'blog':
            webpage['@type'] = 'CollectionPage'
            webpage['mainEntity'] = {'@id': url+'#articole'}
            cards = list(main.all(lambda n: n.tag == 'article' and has_class(n, 'blog-card')))
            items = []
            for position, card in enumerate(cards, 1):
                link = card.first(lambda n: n.tag == 'h3').first(lambda n: n.tag == 'a')
                items.append({'@type': 'ListItem', 'position': position, 'name': link.text(),
                              'url': urljoin(url, link.attrs['href'])})
            graph.append({'@type': 'ItemList', '@id': url+'#articole', 'name': 'Articole PPW',
                          'numberOfItems': len(items), 'itemListElement': items})

        elif kind == 'profile':
            people = []
            for script in doc.all(lambda n: n.tag == 'script' and n.attrs.get('type') == 'application/ld+json'):
                schema = json.loads(''.join(c for c in script.children if isinstance(c, str)))
                nodes = schema.get('@graph', [schema])
                people.extend(n for n in nodes if n.get('@type') == 'Person')
            if len(people) != 1:
                raise ValueError('The team profile must define exactly one factual Person entity.')
            person = people[0]
            webpage['@type'] = 'ProfilePage'
            webpage['mainEntity'] = {'@id': person['@id']}
            person['affiliation'] = {'@type': 'Organization', '@id': organization['@id'], 'name': name, 'url': site}
            person['mainEntityOfPage'] = {'@id': webpage['@id']}
            graph.append(person)
            image = person['image']
            image_alt = person['name']

        else:
            post = main.first(lambda n: n.tag == 'article' and has_class(n, 'post'))
            post_header = post.first(lambda n: n.tag == 'header' and has_class(n, 'post-header'))
            published = post_header.first(lambda n: n.tag == 'time').attrs['datetime']
            modified = post.attrs.get('data-date-modified', meta(doc, 'article:modified_time', published))
            # Persist the original editorial date; never replace it with the build date.
            if 'data-date-modified' not in post.attrs:
                raise ValueError('Article missing authored data-date-modified: '+str(path))
            article = {'@type': 'BlogPosting', '@id': url+'#articol', 'url': url,
                       'headline': heading, 'description': entry['description'],
                       'datePublished': published, 'dateModified': modified,
                       'inLanguage': entry['language'], 'mainEntityOfPage': {'@id': webpage['@id']},
                       'author': {'@type': 'Organization', '@id': organization['@id'], 'name': name, 'url': site},
                       'publisher': publisher}
            body = post.first(lambda n: has_class(n, 'post-body'))
            summary = next(body.all(lambda n: has_class(n, 'post-summary')), None)
            if summary:
                article['abstract'] = ' '.join(item.text() for item in summary.all(lambda n: n.tag == 'li'))
            citations = []
            for link in body.all(lambda n: n.tag == 'a' and 'href' in n.attrs):
                target = urljoin(url, link.attrs['href'])
                parsed = urlsplit(target)
                if (parsed.scheme in {'http', 'https'} and parsed.hostname != urlsplit(site).hostname
                        and parsed.hostname != urlsplit(site).hostname.removeprefix('www.') and target not in citations):
                    citations.append(target)
            if citations:
                article['citation'] = citations
            webpage['mainEntity'] = {'@id': article['@id']}
            pictures = list(post.all(lambda n: n.tag == 'img'))
            if pictures:
                article['image'] = [urljoin(url, picture.attrs['src']) for picture in pictures]
                # Social preview clients generally need a raster image, unlike Google Images.
                if urlsplit(article['image'][0]).path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    image = article['image'][0]
                    image_alt = pictures[0].attrs.get('alt', heading)
            graph.append(article)
            dates = [('article:published_time', published), ('article:modified_time', modified)]

        breadcrumb = next(main.all(lambda n: n.tag == 'nav' and
                                  (has_class(n, 'post-breadcrumb') or has_class(n, 'team-breadcrumb'))), None)
        if breadcrumb:
            items = []
            for node in breadcrumb.children:
                if not hasattr(node, 'tag') or node.attrs.get('aria-hidden') == 'true':
                    continue
                if node.tag == 'a' or node.attrs.get('aria-current') == 'page':
                    items.append({'@type': 'ListItem', 'position': len(items)+1, 'name': node.text(),
                                  'item': urljoin(url, node.attrs['href']) if node.tag == 'a' else url})
            if len(items) >= 2:
                webpage['breadcrumb'] = {'@id': url+'#fir-navigare'}
                graph.append({'@type': 'BreadcrumbList', '@id': url+'#fir-navigare', 'itemListElement': items})

        properties = [('og:type', 'article' if kind == 'article' else 'website'),
                      ('og:locale', 'ro_RO'), ('og:site_name', name), ('og:title', entry['title']),
                      ('og:description', entry['description']), ('og:url', url), ('og:image', image),
                      ('og:image:alt', image_alt), *dates]
        markdown_url = urljoin(url, 'index.md')
        block = '\n'.join([
            '<!-- discovery:start; generated by scripts/build_discovery.py -->',
            f'<link rel="canonical" href="{escape(url, quote=True)}" />',
            '<meta name="robots" content="index, follow, max-image-preview:large" />',
            *(f'<meta property="{key}" content="{escape(value, quote=True)}" />' for key, value in properties),
            '<meta name="twitter:card" content="summary" />',
            f'<meta name="twitter:title" content="{escape(entry["title"], quote=True)}" />',
            f'<meta name="twitter:description" content="{escape(entry["description"], quote=True)}" />',
            f'<meta name="twitter:image" content="{escape(image, quote=True)}" />',
            f'<meta name="twitter:image:alt" content="{escape(image_alt, quote=True)}" />',
            f'<link rel="alternate" type="text/markdown" href="{markdown_url}" title="Conținut în format Markdown" />',
            f'<link rel="describedby" href="{site}llms.txt" type="text/plain" />',
            f'<link rel="sitemap" type="application/xml" href="{site}sitemap.xml" />',
            '<script type="application/ld+json">'+json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, indent=2).replace('</', '<\\/')+'</script>',
            '<!-- discovery:end -->'])

        source = entry['source']
        source = re.sub(r'\s*<!-- discovery:start;.*?<!-- discovery:end -->', '', source, flags=re.S)
        source = re.sub(r'\s*<!-- fonts:start -->.*?<!-- fonts:end -->', '', source, flags=re.S)
        head, body = source.split('</head>', 1)
        head = re.sub(r'\s*<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>.*?</script>', '', head, flags=re.S)

        def strip_managed(match):
            tag = Document(match[0]).root.children[0]
            if tag.tag == 'meta':
                if tag.attrs.get('property', '').startswith(('og:', 'article:')) or tag.attrs.get('name', '').startswith('twitter:') or tag.attrs.get('name') == 'robots':
                    return ''
            elif tag.tag == 'link':
                rel = tag.attrs.get('rel', '')
                if rel in {'canonical', 'describedby', 'sitemap'} or (rel == 'alternate' and tag.attrs.get('type') == 'text/markdown'):
                    return ''
            return match[0]

        head = re.sub(r'<(?:meta|link)\b[^>]*>', strip_managed, head)
        fonts = '\n'.join(['<!-- fonts:start -->',
            '<link rel="preconnect" href="https://fonts.googleapis.com" />',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />',
            f'<link rel="stylesheet" href="{escape(FONT_URL, quote=True)}" />', '<!-- fonts:end -->'])
        head = re.sub(r'<link\b(?=[^>]*rel="stylesheet")[^>]*>', lambda m: fonts+'\n'+m[0], head, count=1)

        def version_asset(match):
            prefix, href = match[1], match[2]
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc:
                return match[0]
            asset = (path.parent/parsed.path).resolve()
            if asset.is_relative_to(root) and asset.is_file() and asset.suffix in {'.css', '.js'}:
                return prefix+parsed.path+'?v='+sha256(asset.read_bytes()).hexdigest()[:12]+'"'
            return match[0]

        head = re.sub(r'((?:src|href)=")([^"]+)"', version_asset, head)
        head = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', head)
        path.write_text(head.rstrip()+'\n'+block+'\n</head>'+body, encoding='utf-8')
