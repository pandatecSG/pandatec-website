# PANDATEC static website

Static GitHub Pages export. Open index.html or publish this folder through GitHub Pages. WordPress-only functions are not included.

## Product category menus (required for every category)

Every product category page (level 2 and level 3) must show the category menu.

To add a new category:
1. Create the folder, e.g. `products/ppe-safety/<new-category>/index.html`.
2. Run `python .github/scripts/category_menus.py build`. The new category is added to `.github/category-menu.json` and the menu is rebuilt on every category page of that group.
3. To change a menu label or order, edit `.github/category-menu.json`, then run the build command again.

The GitHub check "Category menu check" runs on every push and fails if a category page has no menu or an outdated menu.

## Old Google URLs (no redirects)

Old WordPress URLs that still get Google impressions are listed in `.github/legacy-pages.json` (`"/old/path/": "/new/path/"`).
`python .github/scripts/legacy_pages.py build` writes each old URL as a copy of its new page; the copy keeps the new page's canonical link, so Google moves the old URL's ranking to the new page. The copies are not in sitemap.xml or the site search, and the "Build All products catalogue" workflow refreshes them on every push. To add an old URL, add a line to the JSON and run the build command.
