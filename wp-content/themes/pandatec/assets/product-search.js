(function () {
  'use strict';

  var forms = document.querySelectorAll('[data-product-search]');
  if (!forms.length) return;

  var productData;
  var loading;

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>'"]/g, function (character) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;', '"':'&quot;'}[character];
    });
  }

  function loadProducts() {
    if (!loading) {
      loading = fetch('/pandatec-website/product-data.json')
        .then(function (response) {
          if (!response.ok) throw new Error('Product data could not be loaded.');
          return response.json();
        })
        .then(function (data) {
          productData = Array.isArray(data) ? data : (data.products || []);
          return productData;
        });
    }
    return loading;
  }

  function showResults(container, query, results) {
    if (!container) return;
    var html = results.length ? results.map(function (product) {
      var slug = product.slug || '';
      var title = product.name || product.sku || 'Product';
      var details = [product.sku, product.category, product.subcategory || product.sub_category, product.level3].filter(Boolean).join(' · ');
      return '<a class="search-result" href="/pandatec-website/product/' + encodeURIComponent(slug) + '/">' +
        '<strong>' + escapeHtml(title) + '</strong>' +
        (details ? '<small>' + escapeHtml(details) + '</small>' : '') +
        '</a>';
    }).join('') : '<p class="search-no-results">No matching products found for “' + escapeHtml(query) + '”.</p>';
    container.innerHTML = html;
    container.classList.add('is-visible');
  }

  forms.forEach(function (form, index) {
    var input = form.querySelector('input[type="search"]');
    var resultsBox = form.parentElement.querySelector('[data-search-results]');
    if (!input) return;
    if (!input.id) input.id = 'product-search-' + index;

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var query = input.value.trim();
      if (!query) {
        input.focus();
        return;
      }
      if (resultsBox) {
        resultsBox.textContent = 'Searching products…';
        resultsBox.classList.add('is-visible');
      }
      loadProducts().then(function (products) {
        var needle = query.toLowerCase();
        var results = products.filter(function (product) {
          return ['name', 'sku', 'category', 'subcategory', 'sub_category', 'level3', 'short_description', 'description']
            .some(function (field) { return String(product[field] || '').toLowerCase().indexOf(needle) !== -1; });
        }).slice(0, 12);
        showResults(resultsBox, query, results);
      }).catch(function () {
        if (resultsBox) {
          resultsBox.textContent = 'Search is temporarily unavailable. Please try again.';
          resultsBox.classList.add('is-visible');
        }
      });
    });
  });
}());
