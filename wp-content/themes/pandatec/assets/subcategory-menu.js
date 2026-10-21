(function () {
  document.querySelectorAll('.product-card img').forEach(function (image) {
    image.addEventListener('error', function () {
      const pending = document.createElement('div');
      pending.className = 'product-photo image-pending';
      pending.textContent = 'Image pending';
      image.replaceWith(pending);
    }, { once: true });
  });
})();
