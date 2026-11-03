"""Keep site-wide category, product and industry figures in sync with the catalogue.

  python .github/scripts/site_sync.py build   # rewrite every <!--sync:NAME--> block
  python .github/scripts/site_sync.py check   # fail if an L1 is missing card data, an FAQ entry or an llms.txt entry

Sources of truth
  .github/category-menu.json  L1 categories; each L1 needs "card": {order, image, icon, tagline, summary}
  product-data.json           products listed online (unique slugs)
  industries/<name>/          industry pages

Blocks (any page outside /product/):
  l1-cards        full category card grid (Home, All products, Capabilities pages)
  l1-about-cards  About page "What We Source" grid
  l1-count        number of L1 categories, e.g. 10
  l1-count-word   number of L1 categories in words, e.g. Ten
  product-count   products listed online, e.g. 1,907
  industry-count  number of industry pages, e.g. 9
Content checks: every L1 must be linked in the FAQ "Product Category FAQs" section and in llms.txt.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".github" / "category-menu.json"
DATA = ROOT / "product-data.json"
CARD_FIELDS = ("order", "image", "icon", "tagline", "summary")
BLOCK_RE = re.compile(r"<!--sync:([a-z0-9-]+)-->(.*?)<!--/sync:\1-->", re.S)
WORDS = "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen Twenty".split()


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def categories(problems: list[str]) -> list[tuple[str, dict]]:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    out = []
    for slug, c1 in cfg.items():
        card = c1.get("card") or {}
        missing = [f for f in CARD_FIELDS if card.get(f) in (None, "")]
        if missing:
            problems.append(f'category-menu.json: "{slug}" card is missing {", ".join(missing)}')
            continue
        if not (ROOT / "products" / slug / "index.html").is_file():
            problems.append(f"category-menu.json: products/{slug}/index.html does not exist")
            continue
        out.append((slug, c1))
    return sorted(out, key=lambda x: x[1]["card"]["order"])


def blocks(cats: list[tuple[str, dict]]) -> dict[str, str]:
    products = json.loads(DATA.read_text(encoding="utf-8"))
    n_products = len({p["slug"] for p in products if p.get("slug")})
    n_industries = sum(1 for p in (ROOT / "industries").glob("*/index.html"))
    n = len(cats)
    return {
        "l1-cards": "".join(
            f'<article class="category-card"><img src="{c["card"]["image"]}" alt="{html.escape(c["label"])} products supplied by PANDA COLLECTIONS" loading="lazy"><div>'
            f'<span class="category-icon">{c["card"]["icon"]}</span>'
            f'<h3><a href="/products/{s}/">{esc(c["label"])}</a></h3><p>{esc(c["card"]["tagline"])}</p></div></article>'
            for s, c in cats
        ),
        "l1-about-cards": "".join(
            f'<a href="/products/{s}/"><h3>{esc(c["label"])}</h3><p>{esc(c["card"]["summary"])}</p></a>' for s, c in cats
        ),
        "l1-count": str(n),
        "l1-count-word": WORDS[n] if n < len(WORDS) else str(n),
        "product-count": f"{n_products:,}",
        "industry-count": str(n_industries),
    }


def pages():
    for page in sorted(ROOT.glob("**/index.html")):
        rel = page.relative_to(ROOT).parts
        if rel[0] in {"product", ".git", "wp-content"}:
            continue
        yield page


def content_checks(cats, problems):
    faq = (ROOT / "faq" / "index.html").read_text(encoding="utf-8")
    start = faq.find("Product Category FAQs")
    section = faq[start: faq.find("</section>", start)] if start != -1 else ""
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    for slug, c in cats:
        if f'href="/products/{slug}/"' not in section:
            problems.append(f'faq/index.html: no Product Category FAQ links to {c["label"]} (/products/{slug}/)')
        if f"https://pandatec.sg/products/{slug}/)" not in llms:
            problems.append(f'llms.txt: {c["label"]} (/products/{slug}/) is not listed')


def main(mode: str) -> int:
    problems: list[str] = []
    cats = categories(problems)
    values = blocks(cats)
    changed = 0
    for page in pages():
        src = page.read_text(encoding="utf-8")
        if "<!--sync:" not in src:
            continue

        def fill(m):
            name = m.group(1)
            if name not in values:
                problems.append(f"{page.relative_to(ROOT)}: unknown sync block {name}")
                return m.group(0)
            return f"<!--sync:{name}-->{values[name]}<!--/sync:{name}-->"

        out = BLOCK_RE.sub(fill, src)
        if out != src:
            if mode == "build":
                page.write_text(out, encoding="utf-8", newline="")
                changed += 1
            else:
                print(f"WARNING: {page.relative_to(ROOT)}: synced figures are outdated; the Build workflow updates them on push")
    content_checks(cats, problems)
    print(f"{len(cats)} categories, {values['product-count']} products, {values['industry-count']} industries" +
          (f"; pages updated: {changed}" if mode == "build" else ""))
    for p in problems:
        print("ERROR:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
