/* Home Sections management */
(function () {
  var sectionsTbody = document.getElementById('home-sections-tbody');
  var addBtn = document.getElementById('add-section-btn');
  var addModal = document.getElementById('home-section-modal');
  var editModal = document.getElementById('home-section-edit-modal');
  var addForm = document.getElementById('home-section-form');
  var editForm = document.getElementById('home-section-edit-form');

  if (!sectionsTbody) return;

  function getCsrf() {
    return typeof CsrfModule !== 'undefined' ? CsrfModule.getCsrfToken() : '';
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function loadSections() {
    fetch('/api/admin/home-sections', {
      headers: { 'X-CSRF-Token': getCsrf() }
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        renderSections(data.sections);
      })
      .catch(function () {
        sectionsTbody.innerHTML = '<tr><td colspan="5" class="loading-cell">Erreur de chargement</td></tr>';
      });
  }

  function renderSections(sections) {
    if (!sections || sections.length === 0) {
      sectionsTbody.innerHTML = '<tr><td colspan="5" class="loading-cell">Aucune section</td></tr>';
      return;
    }
    var html = '';
    var total = sections.length;
    sections.forEach(function (s, idx) {
      var enabledLabel = s.enabled ? 'Activé' : 'Désactivé';
      var enabledClass = s.enabled ? 'status-active' : 'status-inactive';
      var builtinIcon = s.is_builtin ? '<span class="section-builtin-icon" title="Section système">&#x1f512;</span>' : '';
      var isFirst = idx === 0;
      var isLast = idx === total - 1;
      html += '<tr data-section-id="' + s.id + '" data-type="' + escapeHtml(s.section_type) + '">';
      html += '<td class="order-cell">';
      html += '<button class="btn btn-sm btn-ghost order-btn order-up" data-id="' + s.id + '" ' + (isFirst ? 'disabled' : '') + ' title="Monter">&#9650;</button>';
      html += '<span class="order-num">' + (idx + 1) + '</span>';
      html += '<button class="btn btn-sm btn-ghost order-btn order-down" data-id="' + s.id + '" ' + (isLast ? 'disabled' : '') + ' title="Descendre">&#9660;</button>';
      html += '</td>';
      html += '<td>' + escapeHtml(s.title) + ' ' + builtinIcon + '</td>';
      html += '<td><span class="section-type-badge">' + escapeHtml(s.section_type) + '</span></td>';
      html += '<td><span class="status-badge ' + enabledClass + '">' + enabledLabel + '</span></td>';
      html += '<td>';
      html += '<button class="btn btn-sm btn-ghost section-toggle-btn" data-id="' + s.id + '" data-enabled="' + s.enabled + '">' + (s.enabled ? 'Désactiver' : 'Activer') + '</button> ';
      if (!s.is_builtin) {
        html += '<button class="btn btn-sm btn-ghost section-edit-btn" data-id="' + s.id + '" data-title="' + escapeHtml(s.title) + '" data-content="' + escapeHtml(s.content || '') + '">Modifier</button> ';
        html += '<button class="btn btn-sm btn-danger section-delete-btn" data-id="' + s.id + '">Suppr.</button>';
      }
      html += '</td>';
      html += '</tr>';
    });
    sectionsTbody.innerHTML = html;
    bindSectionEvents();
    bindOrderButtons();
  }

  function moveRow(id, direction) {
    var rows = sectionsTbody.querySelectorAll('tr[data-section-id]');
    var idx = -1;
    for (var i = 0; i < rows.length; i++) {
      if (parseInt(rows[i].getAttribute('data-section-id')) === id) { idx = i; break; }
    }
    if (idx === -1) return;
    if (direction === 'up' && idx === 0) return;
    if (direction === 'down' && idx === rows.length - 1) return;

    var targetIdx = direction === 'up' ? idx - 1 : idx + 1;
    var currentRow = rows[idx];
    var targetRow = rows[targetIdx];

    if (direction === 'up') {
      targetRow.parentNode.insertBefore(currentRow, targetRow);
    } else {
      targetRow.parentNode.insertBefore(currentRow, targetRow.nextSibling);
    }

    var order = [];
    sectionsTbody.querySelectorAll('tr[data-section-id]').forEach(function (row) {
      order.push(parseInt(row.getAttribute('data-section-id')));
    });

    fetch('/api/admin/home-sections/reorder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf() },
      body: JSON.stringify({ order: order }),
    }).then(function () { loadSections(); });
  }

  function bindSectionEvents() {
    /* Toggle */
    sectionsTbody.querySelectorAll('.section-toggle-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = this.getAttribute('data-id');
        var enabled = this.getAttribute('data-enabled') === 'true';
        fetch('/api/admin/home-sections/' + id, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf() },
          body: JSON.stringify({ enabled: !enabled }),
        })
          .then(function (r) { return r.json(); })
          .then(function () { loadSections(); });
      });
    });

    /* Edit */
    sectionsTbody.querySelectorAll('.section-edit-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.getElementById('home-section-edit-id').value = this.getAttribute('data-id');
        document.getElementById('home-section-edit-title').value = this.getAttribute('data-title');
        document.getElementById('home-section-edit-error').classList.add('hidden-section');
        var content = this.getAttribute('data-content') || '';
        if (editorContent) editorContent.innerHTML = content;
        editModal.classList.remove('hidden-section');
        if (editorContent) editorContent.focus();
      });
    });

    /* Delete */
    sectionsTbody.querySelectorAll('.section-delete-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (!confirm('Supprimer cette section personnalisée ?')) return;
        var id = this.getAttribute('data-id');
        fetch('/api/admin/home-sections/' + id, {
          method: 'DELETE',
          headers: { 'X-CSRF-Token': getCsrf() },
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            loadSections();
          });
      });
    });
  }

  function bindOrderButtons() {
    sectionsTbody.querySelectorAll('.order-up').forEach(function (btn) {
      btn.addEventListener('click', function () {
        moveRow(parseInt(this.getAttribute('data-id')), 'up');
      });
    });
    sectionsTbody.querySelectorAll('.order-down').forEach(function (btn) {
      btn.addEventListener('click', function () {
        moveRow(parseInt(this.getAttribute('data-id')), 'down');
      });
    });
  }

  /* ── Add section modal ── */
  if (addBtn && addModal) {
    addBtn.addEventListener('click', function () {
      document.getElementById('home-section-type').value = '';
      document.getElementById('home-section-title').value = '';
      document.getElementById('home-section-error').classList.add('hidden-section');
      addModal.classList.remove('hidden-section');
    });
    document.getElementById('home-section-modal-close').addEventListener('click', function () {
      addModal.classList.add('hidden-section');
    });
    document.getElementById('home-section-cancel').addEventListener('click', function () {
      addModal.classList.add('hidden-section');
    });
    addModal.addEventListener('click', function (e) {
      if (e.target === addModal) addModal.classList.add('hidden-section');
    });
    addForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var sectionType = document.getElementById('home-section-type').value.trim();
      var title = document.getElementById('home-section-title').value.trim();
      if (!sectionType || !title) return;
      fetch('/api/admin/home-sections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf() },
        body: JSON.stringify({ section_type: sectionType, title: title }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.error) {
            document.getElementById('home-section-error').textContent = data.error;
            document.getElementById('home-section-error').classList.remove('hidden-section');
            return;
          }
          addModal.classList.add('hidden-section');
          loadSections();
        });
    });
  }

  /* ── Edit section modal ── */
  if (editModal) {
    var editorContent = document.getElementById('editor-content');
    var editorSource = document.getElementById('editor-source');

    document.getElementById('home-section-edit-close').addEventListener('click', function () {
      editModal.classList.add('hidden-section');
    });
    document.getElementById('home-section-edit-cancel').addEventListener('click', function () {
      editModal.classList.add('hidden-section');
    });
    editModal.addEventListener('click', function (e) {
      if (e.target === editModal) editModal.classList.add('hidden-section');
    });

    /* Toolbar commands */
    document.querySelectorAll('#editor-toolbar .editor-btn[data-cmd]').forEach(function (btn) {
      btn.addEventListener('mousedown', function (e) {
        e.preventDefault();
        editorContent.focus();
        var cmd = this.getAttribute('data-cmd');
        var val = this.getAttribute('data-val') || null;
        document.execCommand(cmd, false, val);
      });
    });

    /* Insert link */
    document.getElementById('editor-insert-link').addEventListener('click', function () {
      editorContent.focus();
      var url = prompt('Entrez l\'URL du lien :', 'https://');
      if (url) {
        document.execCommand('createLink', false, url);
      }
    });

    /* Insert image */
    document.getElementById('editor-insert-image').addEventListener('click', function () {
      editorContent.focus();
      var url = prompt('URL de l\'image :', 'https://');
      var align = prompt('Position (left, center, right) :', 'center') || 'center';
      if (url) {
        var html = '<div style="text-align:' + align + ';"><img src="' + escapeHtml(url) + '" style="max-width:100%;height:auto;" /></div>';
        document.execCommand('insertHTML', false, html);
      }
    });

    /* Insert video */
    document.getElementById('editor-insert-video').addEventListener('click', function () {
      editorContent.focus();
      var url = prompt('URL de la vidéo (YouTube, Vimeo, ou fichier) :', 'https://www.youtube.com/watch?v=');
      var align = prompt('Position (left, center, right) :', 'center') || 'center';
      if (url) {
        var embedUrl = url;
        var match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
        if (match) {
          embedUrl = 'https://www.youtube.com/embed/' + match[1];
        }
        var html = '<div style="text-align:' + align + ';"><div class="responsive-video"><iframe src="' + escapeHtml(embedUrl) + '" frameborder="0" allowfullscreen></iframe></div></div>';
        document.execCommand('insertHTML', false, html);
      }
    });

    /* ── Templates ── */
    document.querySelectorAll('.editor-template').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var tpl = this.getAttribute('data-template');
        var blocks = TEMPLATES[tpl];
        if (!blocks) return;
        var html = renderBlocks(blocks);
        editorContent.focus();
        insertAtCursor(editorContent, html);
      });
    });

    function insertAtCursor(el, html) {
      if (window.getSelection) {
        var sel = window.getSelection();
        if (sel.getRangeAt && sel.rangeCount) {
          var range = sel.getRangeAt(0);
          range.deleteContents();
          var fragment = range.createContextualFragment(html);
          range.insertNode(fragment);
          range.collapse(false);
          sel.removeAllRanges();
          sel.addRange(range);
          return;
        }
      }
      el.focus();
      document.execCommand('insertHTML', false, html);
    }

    /* ── Template system ──
     * Chaque template est un tableau de blocs.
     * Types de blocs disponibles :
     *   hero   : {type:"hero", title, subtitle, btn, btnUrl}
     *   cards  : {type:"cards", cols:2|3, items:[{title, desc, btn, btnUrl}]}
     *   row    : {type:"row", items:[{type:"text", content}, {type:"image", src}]}
     *   list   : {type:"list", items:[{title, desc}]}
     *   text   : {type:"text", content, align}
     *   video  : {type:"video", url, align}
     */
    var TEMPLATES = {
      hero: [
        {type:"hero", title:"Titre de la bannière", subtitle:"Sous-titre accrocheur.", btn:"Bouton", btnUrl:"#"}
      ],
      cards2: [
        {type:"cards", cols:2, items:[
          {title:"Carte 1", desc:"Description première carte.", btn:"En savoir plus"},
          {title:"Carte 2", desc:"Description deuxième carte.", btn:"En savoir plus"}
        ]}
      ],
      cards3: [
        {type:"cards", cols:3, items:[
          {title:"Carte 1", desc:"Description."},
          {title:"Carte 2", desc:"Description."},
          {title:"Carte 3", desc:"Description."}
        ]}
      ],
      "text-img": [
        {type:"row", items:[
          {type:"text", content:"<h3>Titre</h3><p>Texte descriptif.</p>"},
          {type:"image", src:"https://placehold.co/400x250/EEE/999?text=Image"}
        ]}
      ],
      benefits: [
        {type:"list", items:[
          {title:"Avantage 1", desc:"Description avantage 1."},
          {title:"Avantage 2", desc:"Description avantage 2."},
          {title:"Avantage 3", desc:"Description avantage 3."},
          {title:"Avantage 4", desc:"Description avantage 4."}
        ]}
      ]
    };

    function renderBlocks(blocks) {
      var out = '';
      blocks.forEach(function (b) {
        out += renderBlock(b);
      });
      return out;
    }

    function renderBlock(b) {
      switch (b.type) {
        case 'hero':
          return fillTpl('tpl-hero', {
            title: esc(b.title||'Titre'),
            subtitle: esc(b.subtitle||''),
            btn: esc(b.btn||''),
            btnUrl: esc(b.btnUrl||'#')
          });

        case 'cards':
          var colPct = b.cols === 2 ? 'calc(50% - 16px)' : 'calc(33.33% - 16px)';
          var cards = (b.items||[]).map(function(item) {
            return fillTpl('tpl-card', {
              width: colPct,
              title: esc(item.title),
              desc: esc(item.desc||''),
              btn: esc(item.btn||'')
            });
          }).join('');
          return fillTpl('tpl-cards', {cards: cards});

        case 'row':
          var cols = (b.items||[]).map(function(item) {
            if (item.type === 'image') {
              return fillTpl('tpl-col-image', {src: esc(item.src)});
            }
            return fillTpl('tpl-col-text', {content: item.content||''});
          }).join('');
          return fillTpl('tpl-row', {columns: cols});

        case 'list':
          var items = (b.items||[]).map(function(item) {
            return fillTpl('tpl-list-item', {
              title: esc(item.title),
              desc: esc(item.desc||'')
            });
          }).join('');
          return fillTpl('tpl-list', {items: items});

        case 'text':
          return fillTpl('tpl-text', {
            align: b.align||'left',
            content: b.content||''
          });

        case 'video':
          var embedUrl = b.url;
          var m = b.url && b.url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
          if (m) embedUrl = 'https://www.youtube.com/embed/' + m[1];
          return fillTpl('tpl-video', {
            align: b.align||'center',
            url: esc(embedUrl)
          });

        default:
          return '';
      }
    }

    /* ── Template helper ──
     * Prend l'innerHTML d'une balise <script type="text/template" id="tpl-XXX">
     * et remplace les {{clef}} par les valeurs fournies.
     * Pour ajouter un nouveau bloc :
     *   1. Créer un <script type="text/template" id="tpl-monbloc"> dans home_section_blocks.html
     *   2. Ajouter un case 'monbloc' dans renderBlock ci-dessus
     */
    function fillTpl(tplId, vars) {
      var el = document.getElementById(tplId);
      if (!el) return '';
      var html = el.innerHTML.trim();
      for (var key in vars) {
        if (vars.hasOwnProperty(key)) {
          html = html.split('{{' + key + '}}').join(vars[key]);
        }
      }
      return html;
    }

    function esc(str) {
      if (!str) return '';
      return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    editForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var id = document.getElementById('home-section-edit-id').value;
      var title = document.getElementById('home-section-edit-title').value.trim();
      var content = editorContent.innerHTML;
      if (!title) return;
      fetch('/api/admin/home-sections/' + id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf() },
        body: JSON.stringify({ title: title, content: content }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.error) {
            document.getElementById('home-section-edit-error').textContent = data.error;
            document.getElementById('home-section-edit-error').classList.remove('hidden-section');
            return;
          }
          editModal.classList.add('hidden-section');
          loadSections();
        });
    });

    /* Load content when editing */
    var origEdit = document.getElementById('home-section-edit-btn');
    /* Override edit button handler in bindSectionEvents */
  }

  /* Init */
  loadSections();
})();