/* item_detail — star rating init + download scroll */
(function () {
  if (window.DOCUMENT_READY_HANDLERS) {
    window.DOCUMENT_READY_HANDLERS.push(function () { StarRatingModule.init(); });
  } else {
    document.addEventListener('DOMContentLoaded', function () { StarRatingModule.init(); });
  }

  var scrollBtns = document.querySelectorAll('.download-actions .scroll-btn');
  for (var i = 0; i < scrollBtns.length; i++) {
    scrollBtns[i].addEventListener('click', function () {
      var target = document.getElementById('techCodeBlock');
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }
})();
