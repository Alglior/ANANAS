/**
 * A.N.A.N.A.S. — Shared pagination renderer
 * Replaces duplicate implementations across moderation, reports, messages, etc.
 */
var PaginationModule = (function () {
  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderPagination(data, containerId, options) {
    var container = document.getElementById(containerId);
    if (!container || data.total_pages <= 1) {
      if (container) container.innerHTML = '';
      return;
    }
    options = options || {};
    var ariaLabel = options.ariaLabel || 'Pagination';
    var navClass = options.navClass || 'pagination';
    var extraAttrs = options.extraAttrs || '';
    var useHref = options.useHref || false;
    var baseUrl = options.baseUrl || '';

    var html = '<nav class="' + navClass + '" aria-label="' + escapeHtml(ariaLabel) + '">';

    if (data.page > 1) {
      if (useHref && baseUrl) {
        html += '<a class="btn btn-outline transition-hover pagination-prev" href="' + baseUrl + '/' + (data.page - 1) + '" ' + extraAttrs + '>&#9664;&nbsp;Pr\u00e9c\u00e9dent</a>';
      } else {
        html += '<a class="btn btn-outline transition-hover pagination-prev" href="#" data-page="' + (data.page - 1) + '" ' + extraAttrs + '>&#9664;&nbsp;Pr\u00e9c\u00e9dent</a>';
      }
    } else {
      html += '<span class="btn btn-outline pagination-prev disabled">&#9664;&nbsp;Pr\u00e9c\u00e9dent</span>';
    }

    html += '<div class="pagination-numbers">';
    for (var i = 0; i < data.page_numbers.length; i++) {
      var p = data.page_numbers[i];
      if (p === '...') {
        html += '<span class="pagination-ellipsis">&hellip;</span>';
      } else if (p === data.page) {
        html += '<span class="pagination-link active">' + p + '</span>';
      } else if (useHref && baseUrl) {
        html += '<a class="pagination-link" href="' + baseUrl + '/' + p + '" ' + extraAttrs + '>' + p + '</a>';
      } else {
        html += '<a class="pagination-link" href="#" data-page="' + p + '" ' + extraAttrs + '>' + p + '</a>';
      }
    }
    html += '</div>';

    if (data.page < data.total_pages) {
      if (useHref && baseUrl) {
        html += '<a class="btn btn-outline transition-hover pagination-next" href="' + baseUrl + '/' + (data.page + 1) + '" ' + extraAttrs + '>Suivant&nbsp;&#9658;</a>';
      } else {
        html += '<a class="btn btn-outline transition-hover pagination-next" href="#" data-page="' + (data.page + 1) + '" ' + extraAttrs + '>Suivant&nbsp;&#9658;</a>';
      }
    } else {
      html += '<span class="btn btn-outline pagination-next disabled">Suivant&nbsp;&#9658;</span>';
    }

    html += '</nav>';
    container.innerHTML = html;
  }

  return { renderPagination: renderPagination };
})();