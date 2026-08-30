/**
 * A.N.A.N.A.S — Upload : video tutorial modal
 */
UploadModule.videoModal = (function () {
  function init() {
    var overlay = document.getElementById('videoModalOverlay');
    var video = document.getElementById('tutoVideo');
    if (!overlay) return;

    var openBtns = document.querySelectorAll('.publications-tuto-btn');
    var closeBtn = document.getElementById('videoModalClose');

    function openModal() {
      overlay.classList.add('open');
      document.body.classList.add('modal-open');
    }

    function closeModal() {
      overlay.classList.remove('open');
      document.body.classList.remove('modal-open');
      if (video) {
        video.pause();
        video.currentTime = 0;
      }
    }

    openBtns.forEach(function (btn) {
      btn.addEventListener('click', openModal);
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
  }

  return { init: init };
})();
