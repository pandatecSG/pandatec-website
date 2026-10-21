(function () {
  const furnitureCategories = [
    ['system-furniture', 'System Furniture'],
    ['office-accessories', 'Office Accessories'],
    ['office-chairs', 'Office Chairs'],
    ['acoustic-pods', 'Acoustic Pods'],
    ['reception-lounge', 'Reception & Breakout'],
    ['luxury-collection', 'Luxury Collection'],
    ['dining-furniture', 'Dining Furniture'],
    ['school-furniture', 'School Furniture'],
    ['outdoor-furniture', 'Outdoor Furniture'],
    ['hotel-accommodation', 'Hotel Accommodation'],
    ['custom-carpentry', 'Custom Carpentry']
  ];

  const industrialCategories = [
    ['mro-consumables', 'MRO Consumables'],
    ['workshop-equipment', 'Workshop Equipment'],
    ['tools-hardware', 'Tools & Hardware'],
    ['fasteners', 'Fasteners'],
    ['electrical-accessories', 'Electrical Accessories'],
    ['cleaning-maintenance', 'Cleaning & Maintenance'],
    ['facility-appliances', 'Electrical Appliance'],
    ['safety-storage-cabinets', 'Safety & Storage Cabinets']
  ];

  function render(selector, categories, base) {
    document.querySelectorAll(selector).forEach(function (menu) {
    const current = menu.getAttribute('data-current-category');
    menu.innerHTML = '<div class="wrap">' + categories.map(function (item) {
      const active = item[0] === current ? ' aria-current="page"' : '';
      return '<a href="/pandatec-website/products/' + base + '/' + item[0] + '/"' + active + '>' + item[1] + '</a>';
    }).join('') + '</div>';
    });
  }

  render('[data-furniture-submenu]', furnitureCategories, 'furniture-workplace');
  render('[data-industrial-submenu]', industrialCategories, 'industrial-products');

  document.querySelectorAll('.product-card img').forEach(function (image) {
    image.addEventListener('error', function () {
      const pending = document.createElement('div');
      pending.className = 'product-photo image-pending';
      pending.textContent = 'Image pending';
      image.replaceWith(pending);
    }, { once: true });
  });
})();
