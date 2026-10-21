"""Category menus for every product category page (L2 and L3).

Rule: every folder products/<L1>/<L2>/ and products/<L1>/<L2>/<L3>/ that has an
index.html must show
  1. the L2 menu of its L1 (class "subcategory-menu"), and
  2. the L3 menu of its L2 (class "l3-menu") when that L2 has L3 folders.

Menu order and labels live in .github/category-menu.json.
  python .github/scripts/category_menus.py build   # add new folders to the config and rewrite menus
  python .github/scripts/category_menus.py check   # fail if any category page is missing or has an outdated menu
"""
import html, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIG = os.path.join(ROOT, '.github', 'category-menu.json')
PRODUCTS = os.path.join(ROOT, 'products')
START, END = '<!--category-menu-->', '<!--/category-menu-->'
OLD_NAV = re.compile(r'<nav class="(?:subcategory-menu[^"]*|l3-menu|florist-menu)"[^>]*>.*?</nav>', re.S)
BLOCK = re.compile(re.escape(START) + '.*?' + re.escape(END), re.S)


def subdirs(path):
    return sorted(d for d in os.listdir(path) if os.path.isfile(os.path.join(path, d, 'index.html')))


def h1_label(path):
    s = open(os.path.join(path, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else os.path.basename(path)


def load():
    return json.load(open(CONFIG, encoding='utf-8')) if os.path.isfile(CONFIG) else {}


def sync(cfg):
    """Append category folders that are not in the config yet (label taken from the page H1)."""
    added = []
    for l1 in subdirs(PRODUCTS):
        c1 = cfg.setdefault(l1, {'label': h1_label(os.path.join(PRODUCTS, l1)), 'children': []})
        known = {c['slug'] for c in c1['children']}
        for l2 in subdirs(os.path.join(PRODUCTS, l1)):
            if l2 not in known:
                c1['children'].append({'slug': l2, 'label': h1_label(os.path.join(PRODUCTS, l1, l2)), 'children': []}); added.append(f'{l1}/{l2}')
        for c2 in c1['children']:
            p2 = os.path.join(PRODUCTS, l1, c2['slug'])
            if not os.path.isdir(p2):
                continue
            known3 = {c['slug'] for c in c2['children']}
            for l3 in subdirs(p2):
                if l3 not in known3:
                    c2['children'].append({'slug': l3, 'label': h1_label(os.path.join(p2, l3))}); added.append(f'{l1}/{c2["slug"]}/{l3}')
    return added


def menu(cfg, l1, l2, l3=None):
    c1 = cfg[l1]
    e = lambda t: html.escape(t, quote=True)
    out = [START, f'<nav class="subcategory-menu" aria-label="{e(c1["label"])} categories"><div class="wrap">']
    for c in c1['children']:
        cur = ' aria-current="page"' if c['slug'] == l2 else ''
        out.append(f'<a href="/products/{l1}/{c["slug"]}/"{cur}>{e(c["label"])}</a>')
    out.append('</div></nav>')
    c2 = next(c for c in c1['children'] if c['slug'] == l2)
    if c2.get('children'):
        out.append(f'<nav class="l3-menu" aria-label="{e(c2["label"])} types"><div class="wrap">')
        cur = '' if l3 else ' aria-current="page"'
        out.append(f'<a href="/products/{l1}/{l2}/"{cur}>All {e(c2["label"])}</a>')
        for c in c2['children']:
            cur = ' aria-current="page"' if c['slug'] == l3 else ''
            out.append(f'<a href="/products/{l1}/{l2}/{c["slug"]}/"{cur}>{e(c["label"])}</a>')
        out.append('</div></nav>')
    out.append(END)
    return ''.join(out)


def pages(cfg):
    for l1, c1 in cfg.items():
        for c2 in c1['children']:
            yield os.path.join(PRODUCTS, l1, c2['slug'], 'index.html'), menu(cfg, l1, c2['slug'])
            for c3 in c2.get('children', []):
                yield os.path.join(PRODUCTS, l1, c2['slug'], c3['slug'], 'index.html'), menu(cfg, l1, c2['slug'], c3['slug'])


def apply(s, block):
    if START in s:
        return BLOCK.sub(lambda m: block, s, 1)
    s = OLD_NAV.sub('', s)
    i = s.find('search-strip')
    j = s.find('</section>', i) + len('</section>') if i != -1 else s.find('<main id="main">') + len('<main id="main">')
    return s[:j] + block + s[j:]


def main(mode):
    cfg = load()
    problems = []
    if mode == 'build':
        added = sync(cfg)
        json.dump(cfg, open(CONFIG, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=2)
        for a in added:
            print('added to config:', a)
    else:
        missing = sync(json.loads(json.dumps(cfg)))
        problems += [f'category folder not in .github/category-menu.json: {m}' for m in missing]
    changed = 0
    for path, block in pages(cfg):
        if not os.path.isfile(path):
            problems.append(f'config lists a category without a page: {os.path.relpath(path, ROOT)}'); continue
        s = open(path, encoding='utf-8').read()
        t = apply(s, block)
        if t != s:
            if mode == 'build':
                open(path, 'w', encoding='utf-8', newline='').write(t); changed += 1
            else:
                problems.append(f'menu missing or outdated: {os.path.relpath(path, ROOT)}')
    if mode == 'build':
        print('pages updated:', changed)
    for p in problems:
        print('ERROR:', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'check'))
