"""Keep old Google-indexed WordPress URLs working without redirects.

  python .github/scripts/legacy_pages.py build   # write each old URL as a copy of its new page
  python .github/scripts/legacy_pages.py check   # fail if a copy is missing or outdated

Mapping: .github/legacy-pages.json  {"pages": {"/old/path/": "/new/path/"}}
Each copy keeps the new page's <link rel="canonical"> (pointing to the new URL), so Google
moves the old URL's ranking to the new page. Copies are not listed in sitemap.xml or the site search.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / '.github' / 'legacy-pages.json'
CANON = re.compile(r'<link rel="canonical" href="https://pandatec\.sg(/[^"]*)">')


def main(mode):
    pages = json.loads(CONFIG.read_text(encoding='utf-8'))['pages']
    problems, written = [], 0
    for old, new in pages.items():
        src = ROOT / new.strip('/') / 'index.html' if new != '/' else ROOT / 'index.html'
        dst = ROOT / old.strip('/') / 'index.html'
        if not src.is_file():
            problems.append(f'{old}: target {new} has no index.html'); continue
        if (ROOT / old.strip('/')).resolve() == src.parent.resolve() or old.startswith(('/products/', '/product/')):
            problems.append(f'{old}: old URL must not be a live site path'); continue
        html = src.read_text(encoding='utf-8')
        m = CANON.search(html)
        if not m or m.group(1) != new:
            problems.append(f'{old}: target {new} canonical is {m.group(1) if m else "missing"}'); continue
        if mode == 'build':
            if not dst.is_file() or dst.read_text(encoding='utf-8') != html:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(html, encoding='utf-8', newline='')
                written += 1
        elif not dst.is_file() or dst.read_text(encoding='utf-8') != html:
            problems.append(f'{old}: copy missing or outdated - run legacy_pages.py build')
    for p in problems:
        print('ERROR', p)
    print(f'{len(pages)} legacy URLs, {written} written')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'check'))
