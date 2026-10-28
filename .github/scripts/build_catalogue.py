"""Rebuild the "All products" grid (#catalogue) on every L1 category page from product-data.json.

Run: python .github/scripts/build_catalogue.py
Every product whose category_slug matches the L1 page is listed, including all L2/L3 sub-categories,
plus products cross-listed into that L1 through "also_in" (see cross_listing.py).
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "product-data.json"
SKIP = {"corporate-gifts", "ppe-safety"}
IMG_DIR = "/wp-content/uploads/products/"
DESC_LEN = 180

SECTION_RE = re.compile(
    r'(<section class="pale" id="catalogue">.*?<p>)\d+ products · prices on request(</p></div><div class="product-grid">)(.*?)(</div></div></section>)',
    re.S,
)


def image_url(value: str) -> str:
    value = value.strip()
    return value if value.startswith("/") else IMG_DIR + value


def card(p: dict) -> str:
    name = html.escape(p["name"])
    url = f"/product/{p['slug']}/"
    text = (p.get("short_description") or p.get("description") or "").replace("\r", " ").replace("\n", " ").strip()
    desc = html.escape(text[:DESC_LEN])
    img = html.escape(image_url(p["image"]))
    return (
        f'<article class="range-card product-card"><img src="{img}" alt="{name} product image" loading="lazy">'
        f'<h3><a href="{url}">{name}</a></h3><p>{desc}</p>'
        f'<a class="text-link" href="{url}">View product →</a></article>'
    )


def main() -> int:
    products = json.loads(DATA.read_text(encoding="utf-8"))
    by_cat: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for p in products:
        if p["slug"] in seen:
            continue
        seen.add(p["slug"])
        by_cat.setdefault(p["category_slug"], []).append(p)
    for p in products:
        for l1 in {t.strip("/").split("/")[0] for t in p.get("also_in", [])} - {p["category_slug"]}:
            if p not in by_cat.setdefault(l1, []):
                by_cat[l1].append(p)

    for cat, items in sorted(by_cat.items()):
        if cat in SKIP:
            continue
        page = ROOT / "products" / cat / "index.html"
        src = page.read_text(encoding="utf-8")
        if not SECTION_RE.search(src):
            raise SystemExit(f"No #catalogue section in {page}")
        grid = "".join(card(p) for p in items)
        out = SECTION_RE.sub(
            lambda m: f"{m.group(1)}{len(items)} products · prices on request{m.group(2)}{grid}{m.group(4)}",
            src,
            count=1,
        )
        if out != src:
            page.write_text(out, encoding="utf-8", newline="")
        print(f"{cat}: {len(items)} products")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
