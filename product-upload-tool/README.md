# PANDATEC Product Upload Tool

This tool is for the simple employee workflow:

1. Copy `PANDATEC_Employee_Product_Input_Template.xlsx` into a new product folder.
2. Create an `images` folder beside it.
3. Complete only the three columns: `SKU`, `Category`, and `Product Description`.
4. Name images using the SKU:
   - Main image: `SKU.jpg`
   - Additional images: `SKU-01.jpg`, `SKU-02.jpg`, `SKU-03.jpg`
5. Double-click `convert_products.bat`. When the black window asks for the new product folder address, paste the address copied from File Explorer and press Enter. No coding is required.

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

The computer must have Python 3 and the `openpyxl` package installed. This is a one-time setup normally completed by the person who prepares the tool. Employees only need to use `convert_products.bat`.
