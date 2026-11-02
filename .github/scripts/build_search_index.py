"""Build /search-index.json for the site search bar ("Find a product or solution").

Run: python .github/scripts/build_search_index.py
Sources (rebuilt automatically on every push by build-catalogue.yml, so new uploads become searchable):
  - product-data.json             -> every product (name, SKU, model, brand, category path, key text)
  - products/**, industries/**, services/** and other top-level pages -> category & solution pages
Output is compact (arrays, trimmed text) so the browser downloads one small file instead of product-data.json.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "product-data.json"
OUT = ROOT / "search-index.json"
IMG_DIR = "/wp-content/uploads/products/"
TEXT_LEN = 260
PAGE_SKIP = {"product", "wp-content", "product-upload-tool", "review", "sitemap", ".github", ".git"}

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
GB_RE = re.compile(r"\bGB(?:/T)?\s*\d[\d.\-]*", re.I)


def clean(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = " ".join(clean(v) for v in value)
    text = html.unescape(TAG_RE.sub(" ", str(value)))
    return SPACE_RE.sub(" ", GB_RE.sub(" ", text)).strip()


def image_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    return value if value.startswith("/") else IMG_DIR + value


def category_path(p: dict) -> str:
    parts = [clean(p.get("category"))]
    sub = clean(p.get("sub_category")) or clean(p.get("subcategory"))
    parts += [s.strip() for s in sub.split(">") if s.strip()]
    level3 = clean(p.get("level3"))
    if level3 and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", level3) and level3 not in parts:
        parts.append(level3)
    return " › ".join(x for x in parts if x)


def product_rows(products: list[dict]) -> list[list[str]]:
    rows, seen = [], set()
    for p in products:
        slug = p.get("slug")
        if not slug or slug in seen:
            continue
        seen.add(slug)
        extra = " ".join(
            clean(p.get(k))
            for k in ("model", "brand", "material", "application", "industries", "short_description", "key_features")
        )
        also = " ".join(t.strip("/").replace("/", " ").replace("-", " ") for t in p.get("also_in", []) or [])
        rows.append([
            clean(p.get("name")) or p.get("sku", ""),
            clean(p.get("sku")),
            slug,
            category_path(p),
            image_url(p.get("image", "")),
            SPACE_RE.sub(" ", f"{extra} {also}").strip()[:TEXT_LEN],
        ])
    return rows


def page_rows() -> list[list[str]]:
    rows = []
    for page in sorted(ROOT.glob("*/**/index.html")):
        rel = page.relative_to(ROOT)
        if rel.parts[0] in PAGE_SKIP:
            continue
        src = page.read_text(encoding="utf-8", errors="ignore")
        if 'name="robots" content="noindex' in src and rel.parts[0] != "products":
            continue
        h1 = H1_RE.search(src)
        title = TITLE_RE.search(src)
        name = clean(h1.group(1)) if h1 else ""
        full_title = clean(title.group(1)).replace("| PANDA COLLECTIONS", "").strip(" |") if title else ""
        if not name:
            name = full_title
        if not name:
            continue
        desc = DESC_RE.search(src)
        url = "/" + "/".join(rel.parts[:-1]) + "/"
        text = f"{full_title} {clean(desc.group(1)) if desc else ''} {' '.join(rel.parts[:-1]).replace('-', ' ')}"
        rows.append([name, url, SPACE_RE.sub(" ", text).strip()[:TEXT_LEN]])
    return rows


def main() -> int:
    products = json.loads(DATA.read_text(encoding="utf-8"))
    index = {"p": product_rows(products), "g": page_rows()}
    out = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != out:
        OUT.write_text(out, encoding="utf-8", newline="")
    print(f"search-index.json: {len(index['p'])} products, {len(index['g'])} pages, {len(out.encode()) // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
