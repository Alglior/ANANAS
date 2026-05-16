/* item_detail — star rating init */
(function () {
  if (window.DOCUMENT_READY_HANDLERS) {
    window.DOCUMENT_READY_HANDLERS.push(function () { StarRatingModule.init(); });
  } else {
    document.addEventListener('DOMContentLoaded', function () { StarRatingModule.init(); });
  }
})();
