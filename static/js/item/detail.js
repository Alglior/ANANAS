/**
 * A.N.A.N.A.S — Item detail : star rating, download scroll, comment pagination, threaded replies
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

  function getCsrfToken() {
    var input = document.querySelector('input[name="_csrf_token"]');
    return input ? input.value : '';
  }
  var csrfToken = getCsrfToken();

  function renderCommentHTML(c, depth) {
    if (depth === undefined) depth = 0;
    var dateStr = c.created_at || '';
    var avatarHtml = '';
    if (c.user_id && c.user_avatar) {
      avatarHtml = '<img src="' + c.user_avatar + '" alt="" class="comment-avatar">';
    } else if (c.user_id) {
      avatarHtml = '<span class="comment-avatar-initials">' + escapeHtml(c.author_name.charAt(0)) + '</span>';
    } else {
      avatarHtml = '<span class="comment-avatar-initials">' + escapeHtml(c.author_name.charAt(0)) + '</span>';
    }
    var authorHtml = c.user_id
      ? '<a href="/profile/' + c.user_id + '" class="comment-author-wrap">' + avatarHtml + '<span class="comment-author-name">' + escapeHtml(c.author_name) + '</span></a>'
      : '<span class="comment-author-wrap">' + avatarHtml + '<span class="comment-author-name">' + escapeHtml(c.author_name) + '</span></span>';
    var html = '<li class="comment-item" data-comment-id="' + c.id + '">' +
      '<div class="comment-body">' +
      '<div class="comment-header">' +
      authorHtml +
      '<span class="comment-date">' + dateStr + '</span>' +
      '</div>' +
      '<div class="comment-text">' + escapeHtml(c.content) + '</div>' +
      '<div class="comment-actions">' +
      '<button class="comment-reply-btn" data-parent-id="' + c.id + '">R\u00e9pondre</button>' +
      '</div>';
    if (c.replies && c.replies.length) {
      html += '<ul class="comment-replies">';
      for (var j = 0; j < c.replies.length; j++) {
        html += renderCommentHTML(c.replies[j], depth + 1);
      }
      html += '</ul>';
    }
    html += '</div></li>';
    return html;
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

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
          return renderCommentHTML(c);
        }).join('');
        PaginationModule.renderPagination(data, 'comment-pagination', { navClass: 'mod-pagination-nav', ariaLabel: 'Pagination des commentaires' });
      });
  }

  function showReplyForm(parentId, anchorEl) {
    var existing = document.querySelector('.reply-form[data-parent-id="' + parentId + '"]');
    if (existing) {
      existing.querySelector('textarea').focus();
      return;
    }

    var form = document.createElement('div');
    form.className = 'reply-form';
    form.setAttribute('data-parent-id', parentId);
    form.innerHTML =
      '<textarea placeholder="\u00c9crire une r\u00e9ponse..." required></textarea>' +
      '<div class="reply-form-actions">' +
      '<button class="btn btn-cancel" type="button">Annuler</button>' +
      '<button class="btn btn-primary" type="button">R\u00e9pondre</button>' +
      '</div>';

    var commentBody = anchorEl.closest('.comment-body');
    if (commentBody) {
      commentBody.parentNode.insertBefore(form, commentBody.nextSibling);
    }
    form.querySelector('textarea').focus();

    form.querySelector('.btn-cancel').addEventListener('click', function () {
      form.remove();
    });

    form.querySelector('.btn-primary').addEventListener('click', function () {
      var text = form.querySelector('textarea').value.trim();
      if (!text) return;

      var btn = this;
      btn.disabled = true;
      btn.textContent = 'Envoi...';

      fetch('/api/catalogue/item/' + itemId + '/reply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRF-Token': csrfToken,
        },
        body: JSON.stringify({ text: text, parent_id: parentId }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.error) {
            btn.disabled = false;
            btn.textContent = 'R\u00e9pondre';
            return;
          }
          var repliesList = anchorEl.closest('.comment-body').querySelector('.comment-replies');
          if (!repliesList) {
            repliesList = document.createElement('ul');
            repliesList.className = 'comment-replies';
            anchorEl.closest('.comment-body').appendChild(repliesList);
          }
          var replyHtml = renderCommentHTML(data);
          repliesList.insertAdjacentHTML('beforeend', replyHtml);
          form.remove();

          var badge = document.querySelector('.comment-count-badge');
          if (badge) {
            var count = parseInt(badge.textContent, 10);
            badge.textContent = count + 1;
          }
        })
        .catch(function () {
          btn.disabled = false;
          btn.textContent = 'R\u00e9pondre';
        });
    });
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest('.pagination-prev, .pagination-next, .pagination-link');
    if (link && e.target.closest('#comment-pagination')) {
      e.preventDefault();
      var href = link.getAttribute('href');
      if (href) {
        loadComments(href.split('?page=')[1] || 1);
      }
      return;
    }

    var replyBtn = e.target.closest('.comment-reply-btn');
    if (replyBtn) {
      e.preventDefault();
      var parentId = parseInt(replyBtn.getAttribute('data-parent-id'), 10);
      showReplyForm(parentId, replyBtn);
    }
  });

  PaginationModule.renderPagination(
    { page: commentPage, total_pages: commentTotalPages, page_numbers: commentPageNumbers },
    'comment-pagination',
    { navClass: 'mod-pagination-nav', ariaLabel: 'Pagination des commentaires' }
  );

  var commentForm = document.querySelector('.comment-form');
  if (commentForm) {
    commentForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var textarea = commentForm.querySelector('textarea');
      var text = textarea.value.trim();
      if (!text) return;

      var btn = commentForm.querySelector('.btn-primary');
      btn.disabled = true;
      btn.textContent = 'Envoi...';

      fetch('/api/catalogue/item/' + itemId + '/reply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRF-Token': csrfToken,
        },
        body: JSON.stringify({ text: text, parent_id: null }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.error) {
            btn.disabled = false;
            btn.textContent = 'Publier';
            return;
          }
          textarea.value = '';
          btn.disabled = false;
          btn.textContent = 'Publier';

          var list = document.getElementById('comments-list');
          var empty = document.querySelector('.comments-empty');
          if (!list) {
            list = document.createElement('ul');
            list.id = 'comments-list';
            list.className = 'comments-list';
            var section = commentForm.closest('.comments-section');
            if (section) {
              if (empty) empty.remove();
              section.insertBefore(list, commentForm);
            }
          }
          if (empty) empty.remove();
          list.insertAdjacentHTML('afterbegin', renderCommentHTML(data));

          var badge = document.querySelector('.comment-count-badge');
          if (badge) {
            var count = parseInt(badge.textContent, 10);
            badge.textContent = count + 1;
          } else {
            var h2 = commentForm.closest('.comments-section').querySelector('h2');
            if (h2) {
              var newBadge = document.createElement('span');
              newBadge.className = 'comment-count-badge';
              newBadge.textContent = '1';
              h2.appendChild(newBadge);
            }
          }
        })
        .catch(function () {
          btn.disabled = false;
          btn.textContent = 'Publier';
        });
    });
  }

  var imagePending = mainEl.getAttribute('data-image-pending') === 'true';
  if (imagePending) {
    var SUMMARY_LABELS = {
      pending: 'En attente',
      downloading: 'T\u00e9l\u00e9chargement du torrent...',
      saving: 'Enregistrement...',
      done: 'Termin\u00e9',
      failed: '\u00c9chec',
      skipped: 'Ignor\u00e9'
    };

    var progressEl = document.getElementById('imageProgress');
    var summaryEl = document.getElementById('imageProgressSummary');

    function getJobText(job) {
      if (job.details) return job.details;
      return SUMMARY_LABELS[job.status] || job.status;
    }

    function renderImageJobs(data) {
      var jobs = data.jobs || [];
      if (summaryEl) {
        if (jobs.length) {
          var done = 0;
          for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].status === 'done') done++;
          }
          summaryEl.textContent = 'T\u00e9l\u00e9chargement des images : ' + done + '/' + jobs.length + ' termin\u00e9s';
        } else {
          summaryEl.textContent = 'T\u00e9l\u00e9chargement des images en cours...';
        }
      }
      if (!progressEl || !jobs.length) return;

      var html = '';
      for (var j = 0; j < jobs.length; j++) {
        var job = jobs[j];
        var label = job.label || 'Image ' + (job.idx + 1);
        var pct = Math.round((job.progress || 0) * 100);
        var bar = '';
        if (job.status === 'downloading' || job.status === 'saving') {
          bar = '<div class="image-job-bar"><div class="image-job-bar-fill" style="width:' + pct + '%"></div></div>';
        }
        html += '<div class="image-job-row ' + escapeHtml(job.status) + '">' +
          '<span class="image-job-label">' + escapeHtml(label) + '</span>' +
          '<span class="image-job-status">' + escapeHtml(getJobText(job)) + '</span>' +
          bar +
          '</div>';
      }
      progressEl.innerHTML = html;
    }

    var pollInterval = setInterval(function () {
      fetch('/api/items/' + itemId + '/image-status', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          renderImageJobs(data);
          if (!data.pending) {
            clearInterval(pollInterval);
            window.location.reload();
          }
        })
        .catch(function () {});
    }, 2000);
  }

  var btnVerify = document.getElementById('btnVerifyItem');
  var btnUnverify = document.getElementById('btnUnverifyItem');
  var verifyStatus = document.getElementById('verifyStatus');

  function handleVerify(status) {
    fetch('/api/items/' + itemId + '/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify({ status: status }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) return;
        if (verifyStatus) verifyStatus.textContent = data.new_status;
      });
  }

  if (btnVerify) {
    btnVerify.addEventListener('click', function () { handleVerify('verified'); });
  }
  if (btnUnverify) {
    btnUnverify.addEventListener('click', function () { handleVerify('unofficial'); });
  }
})();