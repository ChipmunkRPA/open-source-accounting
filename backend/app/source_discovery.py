"""Offline HTML-index candidates. No link is fetched or granted source rights."""
import json
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urldefrag
from .intake_schemas import https_url
from .sec_core.core import canonical, digest, CoreError
from .sec_core.fetch import reject_access_page

VERSION = 'html-index-1'
MAX_LINKS = 10000


def extract(raw, base_url, hosts):
    https_url(base_url)
    if len(raw) > 16_000_000 or urlsplit(base_url).hostname not in hosts:
        raise CoreError('Index is outside the declared family hosts or byte limit')
    reject_access_page(raw)
    items, excluded = {}, {}
    class Index(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.ordinal, self.link, self.ignored = 0, None, []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'base' and 'href' in attrs:
                raise CoreError('HTML base routes require a reviewed discovery adapter')
            if tag in {'script', 'style', 'iframe', 'form', 'noscript', 'template'}:
                self.ignored.append(tag)
            if tag == 'a':
                self.ordinal += 1
                if self.ordinal > MAX_LINKS:
                    raise CoreError('Index link limit exceeded; no partial discovery')
                if self.link is not None:
                    raise CoreError('Nested anchors require index review')
                self.link = (self.ordinal, attrs.get('href'), [], bool(self.ignored))
        def handle_data(self, text):
            if self.link is not None and not self.ignored:
                self.link[2].append(text)
        def handle_endtag(self, tag):
            if tag == 'a' and self.link is not None:
                ordinal, href, texts, hidden = self.link
                self.link = None
                if hidden or not href:
                    reason = 'inactive_or_missing_href'
                else:
                    try:
                        if len(href) > 1500 or any(c.isspace() or ord(c) < 32 for c in href) or '\\' in href:
                            raise ValueError('Invalid href')
                        url, fragment = urldefrag(urljoin(base_url, href))
                        https_url(url)
                        if len(url) > 1500:
                            raise ValueError('Oversized URL')
                        reason = 'outside_family_hosts' if urlsplit(url).hostname not in hosts else None
                        if url == urldefrag(base_url)[0]:
                            reason = 'same_index'
                    except ValueError:
                        reason = 'unsafe_url'
                if reason:
                    excluded[reason] = excluded.get(reason, 0)+1
                    return
                label = ' '.join(''.join(texts).split())
                if len(label) > 2000:
                    raise CoreError('Oversized label; no silent truncation')
                item = items.setdefault(url, {'url': url, 'occurrences': [], 'status': 'unreviewed_candidate',
                                             'work_id': None, 'edition': None, 'effective_from': None})
                item['occurrences'].append({'locator': f'HTML anchor {ordinal}', 'href': href,
                                            'fragment': fragment or None, 'label': label})
            if tag in self.ignored:
                del self.ignored[len(self.ignored)-1-self.ignored[::-1].index(tag):]
    parser = Index()
    parser.feed(raw.decode('utf-8', errors='strict'))
    parser.close()
    if parser.link is not None:
        raise CoreError('Unclosed anchor requires index review')
    return {'adapter_version': VERSION, 'raw_sha256': digest(raw), 'base_url': base_url,
            'items': [items[url] for url in sorted(items)], 'anchors_observed': parser.ordinal,
            'excluded_occurrences': excluded, 'network_requests': 0,
            'coverage_scope': 'links in this exact stored HTML artifact only; not a complete publication inventory'}


def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))
    raw = sys.stdin.buffer.read(16_000_001)
    sys.stdout.buffer.write(canonical(extract(raw, sys.argv[1], json.loads(sys.argv[2]))))


if __name__ == '__main__':
    main()
