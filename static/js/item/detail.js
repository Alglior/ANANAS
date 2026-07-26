/**
 * A.N.A.N.A.S. — Item detail : star rating, download scroll, comment pagination
 */
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

  var mainEl = document.querySelector('.detail-page');
  if (!mainEl) return;

  var itemId = mainEl.getAttribute('data-item-id');
  if (!itemId) return;

  var commentPage = parseInt(mainEl.getAttribute('data-comment-page'), 10) || 1;
  var commentTotalPages = parseInt(mainEl.getAttribute('data-comment-total-pages'), 10) || 1;
  var commentPageNumbersAttr = mainEl.getAttribute('data-comment-page-numbers') || '';
  var commentPageNumbers = commentPageNumbersAttr ? commentPageNumbersAttr.split(',').map(function (s) {
    var n = parseInt(s, 10);
    return isNaN(n) ? s : n;
  }) : [commentPage];

  function loadComments(page) {
    var url = '/catalogue/item/' + itemId + '/comments/json?page=' + page;
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var list = document.getElementById('comments-list');
        if (data.comment_count === 0 || !data.comments.length) {
          list.innerHTML = '';
          return;
        }
        list.innerHTML = data.comments.map(function (c) {
          var dateStr = '';
          if (c.created_at) {
            dateStr = new Date(c.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
          }
          return '<li class="comment-item"><div class="comment-header"><span class="comment-author">' + c.author_name + '</span><span class="comment-date">' + dateStr + '</span></div><p class="comment-text">' + c.content + '</p></li>';
        }).join('');
        PaginationModule.renderPagination(data, 'comment-pagination', { navClass: 'mod-pagination-nav', ariaLabel: 'Pagination des commentaires' });
      });
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest('.pagination-prev, .pagination-next, .pagination-link');
    if (!link || !e.target.closest('#comment-pagination')) return;
    e.preventDefault();
    var href = link.getAttribute('href');
    if (href) {
      loadComments(href.split('?page=')[1] || 1);
    }
  });

  PaginationModule.renderPagination(
    { page: commentPage, total_pages: commentTotalPages, page_numbers: commentPageNumbers },
    'comment-pagination',
    { navClass: 'mod-pagination-nav', ariaLabel: 'Pagination des commentaires' }
  );

  var imagePending = mainEl.getAttribute('data-image-pending') === 'true';
  if (imagePending) {
    var pollInterval = setInterval(function () {
      fetch('/api/items/' + itemId + '/image-status', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.pending) {
            clearInterval(pollInterval);
            window.location.reload();
          }
        })
        .catch(function () {});
    }, 2000);
  }
})();