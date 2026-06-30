import json
import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs, urlunparse
from urllib.request import Request, urlopen


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.title = ""
        self._in_title = False
        self.scripts = []
        self._script_type = ""
        self._in_script = False
        self._script_buf = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "meta":
            key = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
            val = attrs.get("content")
            if key and val:
                self.meta[key.lower()] = unescape(val).strip()
        if tag.lower() == "script":
            self._script_type = (attrs.get("type") or "").lower()
            if "ld+json" in self._script_type:
                self._in_script = True
                self._script_buf = []

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_script:
            self._script_buf.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False
        if tag.lower() == "script" and self._in_script:
            self.scripts.append("".join(self._script_buf).strip())
            self._in_script = False
            self._script_buf = []


class CoupangMetadataExtractor:
    """Safe Coupang link analyzer.

    v3.8 tries normal public metadata extraction only:
    - URL IDs: productId, itemId, vendorItemId
    - HTML meta tags: og:title, og:image, description
    - JSON-LD Product fields when available

    It does not log in, bypass anti-bot systems, or scrape private pages.
    If Coupang blocks the page, the studio falls back to user-entered fields.
    """

    def extract(self, coupang_url='', product_name='', price='', category='', image_url='', partner_url='', fetch=True):
        url = (coupang_url or '').strip()
        parsed = urlparse(url) if url else None
        query = parse_qs(parsed.query) if parsed else {}
        product_id = self._find_product_id(url)
        item_id = self._first(query.get('itemId'))
        vendor_item_id = self._first(query.get('vendorItemId'))
        clean_url = self._clean_url(parsed) if parsed else url

        base = {
            'ok': True,
            'source': 'manual+url',
            'clean_url': clean_url or url,
            'product_id': product_id,
            'item_id': item_id,
            'vendor_item_id': vendor_item_id,
            'product_name': (product_name or '').strip(),
            'price': (price or '').strip(),
            'category': (category or '').strip(),
            'image_url': (image_url or '').strip(),
            'partner_url': (partner_url or '').strip(),
            'description': '',
            'features': [],
            'auto_fetched': False,
            'fetch_status': 'not_requested',
            'memo': '쿠팡이 차단하면 입력값과 URL 식별값으로 안전하게 생성합니다.',
        }
        if not url or not fetch:
            return base

        fetched = self._fetch_public_metadata(url)
        base['fetch_status'] = fetched.get('status', 'unknown')
        base['fetch_error'] = fetched.get('error', '')
        if fetched.get('ok'):
            base['auto_fetched'] = True
            base['source'] = 'manual+url+public_meta'
            if not base['product_name'] and fetched.get('title'):
                base['product_name'] = self._clean_title(fetched.get('title'))
            if not base['image_url'] and fetched.get('image_url'):
                base['image_url'] = fetched.get('image_url')
            if not base['price'] and fetched.get('price'):
                base['price'] = fetched.get('price')
            if not base['description'] and fetched.get('description'):
                base['description'] = fetched.get('description')
            if fetched.get('features'):
                base['features'] = fetched.get('features')[:8]
            base['raw_meta_keys'] = fetched.get('raw_meta_keys', [])[:30]
            base['memo'] = '공개 메타데이터를 읽었습니다. 빈 항목은 사용자가 입력한 값 또는 기본값을 사용합니다.'
        return base

    def _fetch_public_metadata(self, url):
        try:
            req = Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 AutoCommerceAI/3.8 metadata preview',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.6,en;q=0.5',
                },
            )
            with urlopen(req, timeout=8) as resp:
                status = getattr(resp, 'status', 200)
                html = resp.read(1_500_000).decode(resp.headers.get_content_charset() or 'utf-8', errors='ignore')
        except Exception as e:
            return {'ok': False, 'status': 'fetch_failed', 'error': str(e)}

        parser = _MetaParser()
        try:
            parser.feed(html)
        except Exception:
            pass
        meta = parser.meta
        title = meta.get('og:title') or meta.get('twitter:title') or parser.title.strip()
        desc = meta.get('og:description') or meta.get('description') or meta.get('twitter:description') or ''
        image = meta.get('og:image') or meta.get('twitter:image') or meta.get('image') or ''
        price = meta.get('product:price:amount') or meta.get('price') or ''
        features = self._extract_feature_candidates(html)

        for script in parser.scripts[:10]:
            data = self._try_json(script)
            for obj in self._walk_json(data):
                if not isinstance(obj, dict):
                    continue
                typ = obj.get('@type') or obj.get('type')
                typ_text = ' '.join(typ) if isinstance(typ, list) else str(typ or '')
                if 'Product' in typ_text or obj.get('name') or obj.get('offers'):
                    title = title or obj.get('name') or ''
                    image = image or self._first_json(obj.get('image'))
                    desc = desc or obj.get('description') or ''
                    offers = obj.get('offers')
                    if isinstance(offers, dict):
                        price = price or str(offers.get('price') or '')
                    if isinstance(obj.get('brand'), dict):
                        features.append('브랜드: ' + str(obj['brand'].get('name', '')))
        return {
            'ok': bool(title or image or desc or price or features),
            'status': f'http_{status}',
            'title': self._squash(title),
            'description': self._squash(desc),
            'image_url': image,
            'price': self._squash(price),
            'features': [self._squash(x) for x in features if self._squash(x)],
            'raw_meta_keys': sorted(meta.keys()),
        }

    def _extract_feature_candidates(self, html):
        text = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
        text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = unescape(text)
        rows = []
        for line in text.splitlines():
            s = self._squash(line)
            if 8 <= len(s) <= 90 and any(k in s for k in ['무료배송', '쿠팡', '로켓', '상품', '구매', '리뷰', '할인', '배송']):
                if s not in rows:
                    rows.append(s)
            if len(rows) >= 8:
                break
        return rows

    def _try_json(self, text):
        try:
            return json.loads(text)
        except Exception:
            return None

    def _walk_json(self, data):
        if isinstance(data, dict):
            yield data
            for v in data.values():
                yield from self._walk_json(v)
        elif isinstance(data, list):
            for x in data:
                yield from self._walk_json(x)

    def _first_json(self, value):
        if isinstance(value, list):
            return str(value[0]) if value else ''
        return str(value or '')

    def _clean_title(self, title):
        title = self._squash(title)
        title = re.sub(r'\s*[-|]\s*쿠팡.*$', '', title)
        return title.strip()

    def _squash(self, text):
        return re.sub(r'\s+', ' ', str(text or '')).strip()

    def _find_product_id(self, text):
        m = re.search(r'/products/(\d+)', text or '')
        return m.group(1) if m else ''

    def _first(self, values):
        if not values:
            return ''
        return str(values[0])

    def _clean_url(self, parsed):
        if not parsed:
            return ''
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
