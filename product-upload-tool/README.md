# PANDATEC Product Upload Tool

This tool is for the simple employee workflow:

1. Copy `PANDATEC_Employee_Product_Input_Template.xlsx` into a new batch folder.
2. Create an `images` folder beside it.
3. Complete only the three columns: `SKU`, `Category`, and `Product Description`.
4. Name images using the SKU:
   - Main image: `SKU.jpg`
   - Additional images: `SKU-01.jpg`, `SKU-02.jpg`, `SKU-03.jpg`
5. Run the converter:

```text
python convert_products.py "C:\path\to\products\batch_2026-10-14"
```

The tool creates:

- `PANDATEC_Product_Upload_Ready.xlsx` - the complete 31-column upload file.
- `validation_report.txt` - missing images, duplicate SKUs and invalid categories.

Products are created as **Draft**. Review the generated file before importing or publishing products. The converter does not invent technical facts; SEO and AI fields are left for review or later AI processing.

The input folder should look like this:

```text
batch_2026-10-14/
├── images/
│   ├── PT-TD-CHR-318A.jpg
│   ├── PT-TD-CHR-318A-01.jpg
│   └── PT-TD-CHR-318B.jpg
└── products.xlsx
```

Requires Python 3 and the `openpyxl` package:

```text
python -m pip install openpyxl
```
