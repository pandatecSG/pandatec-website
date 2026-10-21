# PANDATEC static website

Static GitHub Pages export. Open index.html or publish this folder through GitHub Pages. WordPress-only functions are not included.

## Product category menus (required for every category)

Every product category page (level 2 and level 3) must show the category menu.

To add a new category:
1. Create the folder, e.g. `products/ppe-safety/<new-category>/index.html`.
2. Run `python .github/scripts/category_menus.py build`. The new category is added to `.github/category-menu.json` and the menu is rebuilt on every category page of that group.
3. To change a menu label or order, edit `.github/category-menu.json`, then run the build command again.

The GitHub check "Category menu check" runs on every push and fails if a category page has no menu or an outdated menu.
