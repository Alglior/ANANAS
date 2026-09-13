(function () {
  var overlay = document.getElementById('pdfModalOverlay');
  if (!overlay) return;

  var iframe = document.getElementById('pdfViewer');
  var titleEl = document.getElementById('pdfModalTitle');
  var downloadBtn = document.getElementById('pdfDownloadBtn');
  var closeBtn = document.getElementById('pdfModalClose');
  var cards = document.querySelectorAll('.rapport-card');

  function openModal(pdfUrl, pdfName) {
    iframe.src = pdfUrl;
    titleEl.textContent = pdfName;
    downloadBtn.href = pdfUrl;
    overlay.classList.add('open');
    document.body.classList.add('modal-open');
  }

  function closeModal() {
    overlay.classList.remove('open');
    document.body.classList.remove('modal-open');
    iframe.src = '';
  }

  cards.forEach(function (card) {
    card.addEventListener('click', function () {
      var pdfUrl = card.getAttribute('data-pdf');
      var pdfName = card.getAttribute('data-name');
      openModal(pdfUrl, pdfName);
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', closeModal);
  }

  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.classList.contains('open')) {
      closeModal();
    }
  });
})();