"""Cross-listing: show one product on several category pages without a second copy.

Each product keeps ONE page (/product/<slug>/) and ONE record in product-data.json.
To show it on other category pages, add to its record:
  "also_in": ["<L1>/<L2>", "<L1>/<L2>/<L3>", ...]
An L3 path also lists the product on that L3's parent L2 page.
Cross-listed cards sit between <!--also-in--> and <!--/also-in--> at the end of the page's
product grid; the "N products" line and the CollectionPage ItemList include them.
  python .github/scripts/cross_listing.py build   # rewrite the cross-listed cards
  python .github/scripts/cross_listing.py check   # fail if a page is outdated or an also_in path has no page
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'product-data.json'
PRODUCTS = ROOT / 'products'
SITE = 'https://pandatec.sg'
IMG_DIR = '/wp-content/uploads/products/'
START, END = '<!--also-in-->', '<!--/also-in-->'
BLOCK = re.compile(re.escape(START) + '.*?' + re.escape(END), re.S)
GRID = '<div class="product-grid">'
LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
DIV = re.compile(r'<div\b|</div>')


def url_of(p):
    return f"/product/{p['slug']}/"


def card(p):
    name = html.escape(p['name'], quote=True)
    url = url_of(p)
    img = (p.get('image') or '').strip()
    if img:
        img = html.escape(img if img.startswith('/') else IMG_DIR + img, quote=True)
        pic = f'<img src="{img}" alt="{name} product image" loading="lazy">'
    else:
        pic = '<div class="product-photo image-pending">Image pending</div>'
    return (f'<article class="range-card product-card">{pic}<h3><a href="{url}">{name}</a></h3>'
            f'<p class="card-sku">{html.escape(p["sku"])}</p><a class="text-link" href="{url}">View product →</a></article>')


def targets(data, problems):
    pages = {}
    for p in data:
        for t in p.get('also_in', []):
            parts = t.strip('/').split('/')
            paths = ['/'.join(parts)] + (['/'.join(parts[:2])] if len(parts) == 3 else [])
            for path in paths:
                page = PRODUCTS / path / 'index.html'
                if len(parts) not in (2, 3) or not page.is_file():
                    problems.append(f'{p["sku"]}: also_in "{t}" has no category page'); break
                lst = pages.setdefault(page, [])
                if p not in lst:
                    lst.append(p)
    return pages


def grid_end(s, i):
    depth = 0
    for m in DIV.finditer(s, i):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            return m.start()
    raise ValueError('product grid not closed')


def render(s, prods, cross_urls):
    s = BLOCK.sub('', s)
    i = s.find(GRID)
    if i == -1:
        raise ValueError('no product grid')
    j = grid_end(s, i)
    grid = s[i:j]
    native = set(re.findall(r'href="(/product/[^"]+/)"', grid))
    add = [p for p in prods if url_of(p) not in native]
    if add:
        s = s[:j] + START + ''.join(card(p) for p in add) + END + s[j:]
    total = grid.count('class="range-card product-card"') + len(add)
    s = re.sub(r'(<p class="updated">[^<]*?)\d+( products)', rf'\g<1>{total}\g<2>', s, count=1)
    s = re.sub(r'(content="[^"]* – )\d+( products)', rf'\g<1>{total}\g<2>', s)

    def fix_ld(m):
        ld = json.loads(m.group(2))
        changed = False
        for node in ld.get('@graph', [ld]):
            lst = node.get('mainEntity') if isinstance(node.get('mainEntity'), dict) else node
            if lst.get('@type') != 'ItemList':
                continue
            old = lst.get('itemListElement', [])
            keep = [e for e in old if not (e.get('url', '').replace(SITE, '') in cross_urls and e.get('url', '').replace(SITE, '') not in native)]
            new = keep + [{'@type': 'ListItem', 'url': SITE + url_of(p), 'name': p['name']} for p in add]
            for n, e in enumerate(new, 1):
                e['position'] = n
            if new != old:
                lst['itemListElement'] = new; changed = True
        return m.group(1) + json.dumps(ld, ensure_ascii=False) + m.group(3) if changed else m.group(0)
    return LD.sub(fix_ld, s)


def main(mode):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    problems = []
    pages = targets(data, problems)
    cross_urls = {url_of(p) for p in data if p.get('also_in')}
    for page in PRODUCTS.rglob('index.html'):
        s = page.read_text(encoding='utf-8')
        if page not in pages and START not in s:
            continue
        t = render(s, pages.get(page, []), cross_urls)
        if t != s:
            if mode == 'build':
                page.write_text(t, encoding='utf-8', newline=''); print('updated:', page.relative_to(ROOT).as_posix())
            else:
                problems.append(f'cross-listing outdated: {page.relative_to(ROOT).as_posix()}')
    for p in problems:
        print('ERROR:', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'check'))
