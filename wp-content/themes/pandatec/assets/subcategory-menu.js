(function () {
  const categories = [
    ['system-furniture', 'System Furniture'],
    ['office-chairs', 'Office Chairs'],
    ['acoustic-pods', 'Acoustic Pods'],
    ['reception-lounge', 'Reception & Lounge'],
    ['luxury-collection', 'Luxury Collection'],
    ['dining-furniture', 'Dining Furniture'],
    ['school-furniture', 'School Furniture'],
    ['outdoor-furniture', 'Outdoor Furniture'],
    ['hotel-accommodation', 'Hotel Accommodation'],
    ['custom-carpentry', 'Custom Carpentry']
  ];

  document.querySelectorAll('[data-furniture-submenu]').forEach(function (menu) {
    const current = menu.getAttribute('data-current-category');
    menu.innerHTML = '<div class="wrap">' + categories.map(function (item) {
      const active = item[0] === current ? ' aria-current="page"' : '';
      return '<a href="/pandatec-website/products/furniture-workplace/' + item[0] + '/"' + active + '>' + item[1] + '</a>';
    }).join('') + '</div>';
  });
})();
