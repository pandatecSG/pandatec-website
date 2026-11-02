(function () {
  'use strict';

  var forms = document.querySelectorAll('[data-product-search]');
  if (!forms.length) return;

  var INDEX_URL = '/search-index.json';
  var PAGE_SIZE = 24;
  var MAX_PAGES = 4;
  var loading;

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>'"]/g, function (c) {
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[c];
    });
  }

  function norm(value) {
    return String(value || '').toLowerCase()
      .normalize('NFKD').replace(/[̀-ͯ]/g, '')
      .replace(/[‘’']/g, '')
      .replace(/&/g, ' and ')
      .replace(/[^a-z0-9一-鿿]+/g, ' ')
      .trim();
  }

  function compact(value) {
    return value.replace(/ /g, '');
  }

  function stem(token) {
    if (token.length > 4 && /ies$/.test(token)) return token.slice(0, -3) + 'y';
    if (token.length > 4 && /(ches|shes|xes|sses)$/.test(token)) return token.slice(0, -2);
    if (token.length > 3 && /[^s]s$/.test(token)) return token.slice(0, -1);
    return token;
  }

  function prepare(fields) {
    return fields.map(function (field) {
      var n = ' ' + norm(field) + ' ';
      return {n: n, c: compact(n)};
    });
  }

  function loadIndex() {
    if (!loading) {
      loading = fetch(INDEX_URL)
        .then(function (response) {
          if (!response.ok) throw new Error('Search index could not be loaded.');
          return response.json();
        })
        .then(function (data) {
          return {
            products: data.p.map(function (r) {
              return {name: r[0], sku: r[1], url: '/product/' + encodeURIComponent(r[2]) + '/', path: r[3], img: r[4], f: prepare([r[0], r[1], r[3], r[5]])};
            }),
            pages: data.g.map(function (r) {
              return {name: r[0], url: r[1], f: prepare([r[0], r[1].replace(/[\/-]/g, ' '), r[2]])};
            })
          };
        });
      loading.catch(function () { loading = null; });
    }
    return loading;
  }

  var PRODUCT_WEIGHTS = [24, 20, 8, 3];
  var PAGE_WEIGHTS = [24, 10, 3];

  function fieldHit(field, token) {
    var at = field.n.indexOf(token);
    if (at !== -1) return field.n.charAt(at - 1) === ' ' ? 2 : 1;
    return field.c.indexOf(token) !== -1 ? 1 : 0;
  }

  function score(record, weights, q) {
    var f = record.f;
    var total = 0;
    var name = f[0];
    if (q.compact.length > 1 && (name.c === q.compact || f[1].c === q.compact)) total += 1000;
    else if (q.compact.length > 2 && (name.c.indexOf(q.compact) === 0 || f[1].c.indexOf(q.compact) === 0)) total += 300;
    else if (q.compact.length > 2 && name.c.indexOf(q.compact) !== -1) total += 150;
    for (var i = 0; i < q.tokens.length; i++) {
      var best = 0;
      var variants = q.tokens[i];
      for (var j = 0; j < f.length; j++) {
        for (var v = 0; v < variants.length; v++) {
          var hit = fieldHit(f[j], variants[v]);
          if (hit) best = Math.max(best, weights[j] * hit);
        }
      }
      if (!best) return total >= 150 ? total : 0;
      total += best;
    }
    return total - Math.min(name.n.length, 120) / 60;
  }

  function parseQuery(raw) {
    var n = norm(raw);
    var tokens = n.split(' ').filter(Boolean).map(function (t) {
      var s = stem(t);
      return s === t ? [t] : [t, s];
    });
    return {tokens: tokens, compact: compact(n)};
  }

  function rank(records, weights, q) {
    var out = [];
    for (var i = 0; i < records.length; i++) {
      var s = score(records[i], weights, q);
      if (s > 0) out.push({r: records[i], s: s});
    }
    out.sort(function (a, b) { return b.s - a.s; });
    return out.map(function (x) { return x.r; });
  }

  function productHtml(p) {
    return '<a class="search-result" href="' + p.url + '">' +
      (p.img ? '<img src="' + escapeHtml(p.img) + '" alt="" loading="lazy" width="56" height="56">' : '<span class="search-thumb"></span>') +
      '<span><strong>' + escapeHtml(p.name) + '</strong><small>' + escapeHtml([p.sku, p.path].filter(Boolean).join(' · ')) + '</small></span></a>';
  }

  function render(box, raw, pages, products, shown) {
    var html = '';
    if (pages.length) {
      html += '<p class="search-heading">Categories &amp; solutions</p><div class="search-pages">' +
        pages.slice(0, 6).map(function (p) { return '<a href="' + p.url + '">' + escapeHtml(p.name) + '</a>'; }).join('') + '</div>';
    }
    if (products.length) {
      html += '<p class="search-heading">' + products.length + (products.length === 1 ? ' product' : ' products') + ' found</p>' +
        products.slice(0, shown).map(productHtml).join('');
      if (products.length > shown && shown < PAGE_SIZE * MAX_PAGES) {
        html += '<button type="button" class="btn secondary search-more" data-search-more>Show more results</button>';
      } else if (products.length > shown) {
        html += '<p class="search-no-results">Showing the top ' + shown + ' results. Add a word or SKU to narrow the search.</p>';
      }
    }
    if (!html) {
      html = '<p class="search-no-results">No matching products found for “' + escapeHtml(raw) + '”. Try another word or a SKU, or <a class="text-link" href="/request-a-quote/">send us your requirement</a>.</p>';
    }
    box.innerHTML = html;
    box.classList.add('is-visible');
  }

  function attach(form, index) {
    var input = form.querySelector('input[type="search"]');
    var box = form.parentElement.querySelector('[data-search-results]');
    if (!input || !box) return null;
    if (!input.id) input.id = 'product-search-' + index;
    input.setAttribute('autocomplete', 'off');
    var timer;
    var state = {raw: '', pages: [], products: [], shown: PAGE_SIZE};

    function run(raw) {
      raw = raw.trim();
      if (!raw) {
        box.classList.remove('is-visible');
        box.innerHTML = '';
        return;
      }
      if (!box.innerHTML) {
        box.textContent = 'Searching products…';
        box.classList.add('is-visible');
      }
      loadIndex().then(function (data) {
        if (raw !== input.value.trim()) return;
        var q = parseQuery(raw);
        if (!q.tokens.length) return;
        state = {raw: raw, pages: rank(data.pages, PAGE_WEIGHTS, q), products: rank(data.products, PRODUCT_WEIGHTS, q), shown: PAGE_SIZE};
        render(box, raw, state.pages, state.products, state.shown);
      }).catch(function () {
        box.textContent = 'Search is temporarily unavailable. Please try again.';
        box.classList.add('is-visible');
      });
    }

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      clearTimeout(timer);
      if (!input.value.trim()) { input.focus(); return; }
      run(input.value);
    });
    input.addEventListener('input', function () {
      clearTimeout(timer);
      var value = input.value;
      timer = setTimeout(function () { if (value.trim().length > 1 || !value.trim()) run(value); }, 180);
    });
    input.addEventListener('focus', function () { loadIndex().catch(function () {}); }, {once: true});
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') { input.value = ''; run(''); }
    });
    box.addEventListener('click', function (event) {
      if (!event.target.closest('[data-search-more]')) return;
      state.shown += PAGE_SIZE;
      render(box, state.raw, state.pages, state.products, state.shown);
    });
    return {input: input, run: run};
  }

  var attached = [];
  forms.forEach(function (form, i) {
    var a = attach(form, i);
    if (a) attached.push(a);
  });

  var initial = new URLSearchParams(location.search).get('s');
  if (initial && attached.length) {
    attached[0].input.value = initial;
    attached[0].run(initial);
  }
}());
