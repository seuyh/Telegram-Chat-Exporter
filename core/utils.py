import re

def sanitize_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.', '(', ')')).strip()

def escape_html(text: str) -> str:
    return (text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

def format_text(text: str) -> str:
    if not text:
        return ""

    def normalize_url(u: str) -> str:
        if u.startswith('www.'):
            return 'http://' + u
        return u

    def repl_md(m):
        label = escape_html(m.group(1))
        url = normalize_url(m.group(2).strip())
        href = escape_html(url)
        return f'<a href="{href}" target="_blank">{label}</a>'

    text = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+|www\.[^\)]+)\)', repl_md, text)

    text = re.sub(r'\*\*(.+?)\*\*', lambda m: f'<strong>{escape_html(m.group(1))}</strong>', text)
    text = re.sub(r'__(.+?)__', lambda m: f'<em>{escape_html(m.group(1))}</em>', text)
    text = re.sub(r'`(.+?)`', lambda m: f'<code>{escape_html(m.group(1))}</code>', text)
    text = re.sub(r'~~(.+?)~~', lambda m: f'<del>{escape_html(m.group(1))}</del>', text)

    url_pattern = r'(https?://[^\s<>"]+|www\.[^\s<>"]+)'

    def repl_url(m):
        url = m.group(1)
        start = m.start()
        context_before = text[max(0, start - 10):start].lower()
        if 'href=' in context_before or '<a ' in context_before:
            return url
        href = normalize_url(url)
        return f'<a href="{escape_html(href)}" target="_blank">{escape_html(url)}</a>'

    text = re.sub(url_pattern, repl_url, text)

    return text