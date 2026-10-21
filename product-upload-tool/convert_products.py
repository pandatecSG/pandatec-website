"""Convert PANDA COLLECTIONS's three-column employee file into the 31-column upload file."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

APPROVED_CATEGORIES = {
    "Furniture & Workplace",
    "Industrial Products & MRO",
    "Building & Infrastructure",
    "Medical & Healthcare",
    "Cleanroom & Controlled Environment",
    "PPE & Safety",
    "Warehouse & Logistics",
    "Machinery & Automation",
}
OUTPUT_HEADERS = [
    "PIC", "* SKU / Product ID", "* Product Name", "* Product Category", "Sub Category",
    "* Product Status", "* Short Description", "Full Product Description", "Key Features",
    "Specifications", "Material", "Dimensions", "Application", "Industries Served", "Brand",
    "Model / Part No.", "MOQ", "Unit", "Country of Origin", "* Image File Name",
    "Additional Image 1", "Additional Image 2", "Additional Image 3", "SEO Title",
    "SEO Keywords", "Meta Description", "URL Slug", "Image Alt Text", "AI Content Instruction",
    "Related SKU", "RFQ Required",
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def clean(value) -> str:
    return "" if value is None else str(value).strip()


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "product"


def product_name(description: str, sku: str) -> str:
    first = re.split(r"[\n.!?。！？]", description, maxsplit=1)[0].strip()
    return (first[:100].rstrip() or sku)


def find_source(folder: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    candidates = sorted(folder.glob("*.xlsx"))
    candidates = [p for p in candidates if not p.name.startswith("PANDATEC_Product_Upload_Ready")]
    if not candidates:
        raise FileNotFoundError("No .xlsx file found in the batch folder.")
    return candidates[0]


def image_index(image_dir: Path) -> dict[str, Path]:
    result = {}
    if not image_dir.exists():
        return result
    for file in image_dir.iterdir():
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
            result[file.name.lower()] = file
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the PANDA COLLECTIONS 31-column product upload file.")
    parser.add_argument("batch_folder", help="Folder containing products.xlsx and an images subfolder")
    parser.add_argument("--excel", help="Optional input Excel path")
    args = parser.parse_args()
    batch = Path(args.batch_folder).expanduser().resolve()
    source = find_source(batch, args.excel)
    image_dir = batch / "images"
    images = image_index(image_dir)
    errors: list[str] = []
    warnings: list[str] = []

    wb_in = load_workbook(source, read_only=True, data_only=True)
    ws_in = wb_in.active
    headers = [clean(c.value).lower() for c in next(ws_in.iter_rows(min_row=1, max_row=1))]
    required = {"sku", "category", "product description"}
    if not required.issubset(headers):
        raise ValueError("The input file must contain exactly these required headers: SKU, Category, Product Description.")
    positions = {name: headers.index(name) for name in required}
    rows = []
    seen: set[str] = set()
    for row_number, row in enumerate(ws_in.iter_rows(min_row=2, values_only=True), start=2):
        sku = clean(row[positions["sku"]]).upper()
        category = clean(row[positions["category"]])
        description = clean(row[positions["product description"]])
        if not sku and not category and not description:
            continue
        if not sku:
            errors.append(f"Row {row_number}: SKU is blank.")
            continue
        if not re.fullmatch(r"[A-Z0-9-]+", sku):
            errors.append(f"Row {row_number}: SKU '{sku}' contains invalid characters.")
        if sku in seen:
            errors.append(f"Row {row_number}: duplicate SKU '{sku}'.")
        seen.add(sku)
        if category not in APPROVED_CATEGORIES:
            errors.append(f"Row {row_number}: category '{category}' is not in the approved list.")
        if not description:
            errors.append(f"Row {row_number}: product description is blank for {sku}.")
        primary = next((images.get(f"{sku}{ext}".lower()) for ext in IMAGE_EXTENSIONS if f"{sku}{ext}".lower() in images), None)
        if not primary:
            errors.append(f"Row {row_number}: missing primary image {sku}.jpg (or .jpeg/.png/.webp).")
        additional = []
        for index in range(1, 4):
            found = next((images.get(f"{sku}-{index:02d}{ext}".lower()) for ext in IMAGE_EXTENSIONS if f"{sku}-{index:02d}{ext}".lower() in images), None)
            additional.append(found.name if found else "")
        rows.append((sku, category, description, primary.name if primary else "", additional))

    report = batch / "validation_report.txt"
    report.write_text(
        "PANDA COLLECTIONS PRODUCT UPLOAD VALIDATION\n\n"
        + ("ERRORS:\n" + "\n".join(f"- {x}" for x in errors) + "\n\n" if errors else "No errors found.\n\n")
        + ("NOTES:\n" + "\n".join(f"- {x}" for x in warnings) + "\n" if warnings else "")
        + f"\nRows detected: {len(rows)}\n",
        encoding="utf-8",
    )
    if errors:
        print(f"Validation failed. See {report}")
        return 2

    wb_out = Workbook()
    ws = wb_out.active
    ws.title = "Product Upload"
    ws.append(OUTPUT_HEADERS)
    for sku, category, description, primary, additional in rows:
        name = product_name(description, sku)
        values = [
            "", sku, name, category, "", "Draft", description[:500], description, "", "", "", "", "", "", "",
            sku, "", "PCS", "", primary, additional[0], additional[1], additional[2], "", "", "", slugify(name),
            f"{name} product image", "Generate accurate product name, key features, specifications, SEO title, keywords and meta description from the supplier description. Do not invent facts.", "", "Yes",
        ]
        ws.append(values)
    header_fill = PatternFill("solid", fgColor="142B4D")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 36
    for column in range(1, len(OUTPUT_HEADERS) + 1):
        ws.column_dimensions[get_column_letter(column)].width = 18
    out = batch / "PANDATEC_Product_Upload_Ready.xlsx"
    wb_out.save(out)
    print(f"Created {out}")
    print(f"Validated {len(rows)} products and matched their images.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
