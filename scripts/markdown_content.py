"""Render visible site content as portable Markdown with absolute source links."""
import re
from urllib.parse import urljoin

IGNORE = {'script', 'style', 'svg', 'form', 'button', 'aside'}


def hidden(node):
    return not isinstance(node, str) and (node.tag in IGNORE or node.attrs.get('aria-hidden') == 'true' or 'hidden' in node.attrs)


def clean(value):
    return re.sub(r'\s+', ' ', value).strip()


def inline_markdown(node, base_url):
    if isinstance(node, str):
        return node
    if hidden(node):
        return ''
    content = ''.join(inline_markdown(child, base_url) for child in node.children)
    if node.tag == 'a':
        target = urljoin(base_url, node.attrs.get('href', ''))
        return '[' + clean(content) + '](' + target + ')'
    if node.tag in {'strong', 'b', 'em', 'i'} and content.strip():
        marker = '**' if node.tag in {'strong', 'b'} else '*'
        return (' ' if content[0].isspace() else '') + marker + content.strip() + marker + (' ' if content[-1].isspace() else '')
    if node.tag == 'code':
        marker = '``' if '`' in content else '`'
        return marker + content + marker
    if node.tag == 'img' and node.attrs.get('alt'):
        return '![' + node.attrs['alt'] + '](' + urljoin(base_url, node.attrs['src']) + ')'
    return content


def raw_text(node):
    return node if isinstance(node, str) else ''.join(raw_text(child) for child in node.children)


def render_markdown(node, base_url):
    """Render nested sections, paragraphs, lists, code, figures and simple tables."""
    def blocks(current):
        if isinstance(current, str) or hidden(current):
            return []
        tag = current.tag
        classes = current.attrs.get('class', '').split()
        if tag == 'nav' and 'post-related' not in classes:
            return []
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            return ['#' * int(tag[1]) + ' ' + clean(inline_markdown(current, base_url))]
        if tag in {'p', 'figcaption', 'summary', 'dt', 'dd'}:
            content = clean(inline_markdown(current, base_url))
            prefix = '### ' if tag == 'summary' else '**' if tag == 'dt' else ''
            suffix = '**' if tag == 'dt' else ''
            return [prefix + content + suffix] if content else []
        if tag == 'a':
            return [clean(inline_markdown(current, base_url))]
        if tag == 'pre':
            code = next(current.all(lambda n: n.tag == 'code'), current)
            language = code.attrs.get('class', '').partition('language-')[2]
            content = raw_text(code).rstrip('\n')
            fence = '````' if '```' in content else '```'
            return [fence + language + '\n' + content + '\n' + fence]
        if tag == 'blockquote':
            content = '\n\n'.join(part for child in current.children for part in blocks(child))
            if not content:
                content = clean(inline_markdown(current, base_url))
            return ['\n'.join('> ' + line if line else '>' for line in content.splitlines())]
        if tag in {'ul', 'ol'}:
            rendered = []
            try:
                start = int(current.attrs.get('start', '1'))
            except ValueError:
                start = 1
            for index, item in enumerate((c for c in current.children if not isinstance(c, str) and c.tag == 'li'), start):
                if hidden(item):
                    continue
                step = next(item.all(lambda n: 'step-icon' in n.attrs.get('class', '').split()), None)
                if step:
                    title = item.first(lambda n: n.tag == 'strong').text()
                    detail = item.first(lambda n: n.tag == 'span' and 'step-icon' not in n.attrs.get('class', '').split()).text()
                    rendered.append(f'{int(step.text())}. **{title}** — {detail}')
                    continue
                block_tags = {'p', 'h2', 'h3', 'h4', 'ul', 'ol', 'div', 'section'}
                parts, pending = [], []
                for child in item.children:
                    if not isinstance(child, str) and child.tag in block_tags:
                        label = clean(''.join(pending))
                        if label:
                            parts.append(label)
                        pending = []
                        parts.extend(blocks(child))
                    else:
                        pending.append(inline_markdown(child, base_url))
                label = clean(''.join(pending))
                if label:
                    parts.append(label)
                content = '\n\n'.join(parts)
                prefix = f'{index}. ' if tag == 'ol' else '- '
                lines = content.splitlines()
                if lines:
                    rendered.append(prefix + lines[0] + ''.join('\n' + (' ' * len(prefix) + line if line else '') for line in lines[1:]))
            return ['\n\n'.join(rendered)] if rendered else []
        if tag == 'table':
            rows = []
            for row in current.all(lambda n: n.tag == 'tr'):
                if hidden(row):
                    continue
                cells = [clean(inline_markdown(cell, base_url)).replace('|', '\\|') for cell in row.children
                         if not isinstance(cell, str) and cell.tag in {'th', 'td'} and not hidden(cell)]
                if cells:
                    rows.append(cells)
            if not rows:
                return []
            width = max(len(row) for row in rows)
            lines = ['| ' + ' | '.join(row + [''] * (width - len(row))) + ' |' for row in rows]
            lines.insert(1, '| ' + ' | '.join(['---'] * width) + ' |')
            caption = next(current.all(lambda n: n.tag == 'caption'), None)
            return ([clean(inline_markdown(caption, base_url))] if caption else []) + ['\n'.join(lines)]
        if tag == 'figure':
            return [clean(inline_markdown(child, base_url)) for child in current.children
                    if not isinstance(child, str) and child.tag in {'img', 'figcaption'} and not hidden(child)]
        if 'post-facts' in classes:
            result = []
            for fact in (child for child in current.children if not isinstance(child, str) and child.tag == 'div'):
                title = fact.first(lambda n: n.tag == 'strong')
                result.append('### ' + clean(inline_markdown(title, base_url)))
                result.extend(part for child in fact.children if child is not title for part in blocks(child))
            return result
        if 'journey-deliverable' in classes:
            return ['**Ce obții:** ' + current.first(lambda n: n.tag == 'strong').text()]
        return [part for child in current.children for part in blocks(child)]

    return '\n\n'.join(part for part in blocks(node) if part).rstrip() + '\n'
