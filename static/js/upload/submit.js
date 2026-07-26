/**
 * A.N.A.N.A.S. — Upload : submit, draft, JSON download, EDITING prefill
 */
UploadModule.submit = (function () {
  var uploadForm = document.getElementById('uploadForm');
  var uploadBtn = document.getElementById('uploadBtn');
  var draftBtn = document.getElementById('draftBtn');
  var uploadStatus = document.getElementById('uploadStatus');

  var spinnerOverlay = document.getElementById('uploadSpinnerOverlay');
  var spinnerText = document.getElementById('spinnerText');
  var spinnerSubtext = document.getElementById('spinnerSubtext');
  var spinnerImagesPending = document.getElementById('spinnerImagesPending');

  function showSpinner(text, subtext, showImages) {
    spinnerText.textContent = text;
    spinnerSubtext.textContent = subtext || '';
    if (showImages) {
      spinnerImagesPending.classList.remove('hidden-section');
    } else {
      spinnerImagesPending.classList.add('hidden-section');
    }
    spinnerOverlay.classList.remove('hidden-section');
    document.body.style.overflow = 'hidden';
  }

  function hideSpinner() {
    spinnerOverlay.classList.add('hidden-section');
    document.body.style.overflow = '';
  }

  async function submitPublish(magnetLinks) {
    var typeSelect = document.getElementById('type');
    var dataInput = document.getElementById('data_input');

    uploadBtn.disabled = true;
    if (draftBtn) draftBtn.disabled = true;

    var title = document.getElementById('title').value.trim();
    if (!title) {
      uploadStatus.textContent = 'Le titre est requis';
      uploadStatus.className = 'form-status form-error';
      uploadBtn.disabled = false;
      if (draftBtn) draftBtn.disabled = false;
      return;
    }

    var isNonData = typeSelect && (typeSelect.value === 'carte' || typeSelect.value === 'application');

    if (!isNonData) {
      var magnetLinksFilled = magnetLinks.filter(function(l) { return l.magnet_link; });
      if (!magnetLinksFilled.length) {
        uploadStatus.textContent = 'Au moins un lien Magnet est requis';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        return;
      }
    }

    if (!UploadModule.EDITING && !isNonData) {
      var dataText = dataInput ? dataInput.value : '';
      var lines = dataText.split('\n').filter(function(line) { return line.trim(); }).slice(0, 50);
      if (!lines.length) {
        uploadStatus.textContent = 'Veuillez coller vos donn\u00e9es';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        return;
      }
    }

    showSpinner(UploadModule.EDITING ? 'Mise \u00e0 jour en cours...' : 'Envoi des donn\u00e9es...', UploadModule.EDITING ? '' : '\u00c9tape 1/2');

    var csrfToken = CsrfModule.getCsrfToken();

    try {
      var chunkId = null;
      if (!UploadModule.EDITING && !isNonData) {
        var formData = new FormData();
        var dataTextValue = dataInput.value;
        var dataLines = dataTextValue.split('\n').filter(function(line) { return line.trim(); }).slice(0, 50);
        formData.append('data_text', dataLines.join('\n'));
        formData.append('title', title);
        formData.append('type', typeSelect.value);
        formData.append('format_type', document.getElementById('format_type').value);
        formData.append('description', document.getElementById('description').value.trim());
        formData.append('data_format_level', 'pack');

        var orgId = document.getElementById('organization_id').value;
        if (orgId) formData.append('organization_id', orgId);
        var lt = document.getElementById('license_type');
        if (lt && lt.value) {
          formData.append('license_type', lt.value);
          if (lt.value === 'other') {
            formData.append('custom_license_text', document.getElementById('custom_license_text').value);
          }
        }

        var fileResult = await UploadModule.payload.safeFetchJson('/api/upload/file', {
          method: 'POST',
          headers: { 'X-CSRF-Token': csrfToken },
          body: formData,
        });
        if (!fileResult.response.ok) {
          hideSpinner();
          uploadStatus.textContent = fileResult.data.error || 'Erreur t\u00e9l\u00e9versement';
          uploadStatus.className = 'form-status form-error';
          uploadBtn.disabled = false;
          if (draftBtn) draftBtn.disabled = false;
          return;
        }
        chunkId = fileResult.data.chunk_id;
      }

      showSpinner(UploadModule.EDITING ? 'Publication du brouillon...' : 'Cr\u00e9ation de l\'item...', UploadModule.EDITING ? '' : '\u00c9tape 2/2');

      var itemPayload = UploadModule.payload.buildItemPayload(magnetLinks, false);
      if (chunkId) itemPayload.chunk_id = chunkId;

      var method = UploadModule.EDITING ? 'PUT' : 'POST';
      var url = UploadModule.EDITING ? '/api/upload/item/' + UploadModule.EDIT_ITEM_ID : '/api/upload/item';

      var itemResult = await UploadModule.payload.safeFetchJson(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        body: JSON.stringify(itemPayload),
      });

      if (!itemResult.response.ok) {
        hideSpinner();
        uploadStatus.textContent = itemResult.data.error || 'Erreur cr\u00e9ation de l\'item';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        return;
      }

      var redirectId = itemResult.data.id || UploadModule.EDIT_ITEM_ID;
      var hasImages = itemPayload.image_magnets && itemPayload.image_magnets.length > 0;
      if (hasImages) {
        showSpinner('Publication r\u00e9ussie !', 'T\u00e9l\u00e9chargement des images en arri\u00e8re-plan...', true);
        setTimeout(function() {
          window.location.href = '/catalogue/item/' + redirectId;
        }, 2000);
      } else {
        showSpinner('Publication r\u00e9ussie !', 'Redirection...');
        setTimeout(function() {
          window.location.href = '/catalogue/item/' + redirectId;
        }, 1500);
      }

    } catch (err) {
      hideSpinner();
      if (err.message === 'SESSION_EXPIRED') {
        uploadStatus.textContent = 'Session expir\u00e9e, veuillez vous reconnecter';
      } else {
        console.error('Erreur de communication:', err);
        uploadStatus.textContent = 'Erreur de communication';
      }
      uploadStatus.className = 'form-status form-error';
      uploadBtn.disabled = false;
      if (draftBtn) draftBtn.disabled = false;
    }
  }

  function initFormSubmission() {
    if (uploadForm) {
      uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        var magnetLinks = UploadModule.magnets.collectLinks();
        submitPublish(magnetLinks);
      });
    }
  }

  function initDraftBtn() {
    if (!draftBtn) return;
    draftBtn.addEventListener('click', async function() {
      var title = document.getElementById('title').value.trim();
      if (!title) {
        uploadStatus.textContent = 'Le titre est requis m\u00eame pour un brouillon';
        uploadStatus.className = 'form-status form-error';
        return;
      }

      draftBtn.disabled = true;
      showSpinner('Enregistrement du brouillon...', '');

      var payload = UploadModule.payload.buildItemPayload([], true);
      payload.status = 'draft';

      var csrfToken = CsrfModule.getCsrfToken();
      var method = UploadModule.EDITING ? 'PUT' : 'POST';
      var url = UploadModule.EDITING ? '/api/upload/item/' + UploadModule.EDIT_ITEM_ID : '/api/upload/item';

      try {
        var result = await UploadModule.payload.safeFetchJson(url, {
          method: method,
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken,
          },
          body: JSON.stringify(payload),
        });
        if (result.response.ok) {
          hideSpinner();
          window.location.href = '/upload?drafts=1';
        } else {
          hideSpinner();
          draftBtn.disabled = false;
          uploadStatus.textContent = result.data.error || 'Erreur';
          uploadStatus.className = 'form-status form-error';
        }
      } catch (err) {
        hideSpinner();
        draftBtn.disabled = false;
        if (err.message === 'SESSION_EXPIRED') {
          uploadStatus.textContent = 'Session expir\u00e9e, veuillez vous reconnecter';
        } else if (err.message === 'NON_JSON_RESPONSE') {
          uploadStatus.textContent = 'Erreur serveur inattendue';
        } else {
          console.error('Erreur r\u00e9seau:', err);
          uploadStatus.textContent = 'Erreur r\u00e9seau';
        }
        uploadStatus.className = 'form-status form-error';
      }
    });
  }

  function initDownloadJson() {
    var downloadJsonBtn = document.getElementById('downloadJsonBtn');
    if (!downloadJsonBtn) return;

    downloadJsonBtn.addEventListener('click', function() {
      var magnetLinks = UploadModule.magnets.collectLinks();
      var payload = UploadModule.payload.buildItemPayload(magnetLinks, false);

      var imageMagnets = UploadModule.imageMagnets.collectLinks();
      if (imageMagnets.length > 0) {
        payload.image_magnets = imageMagnets;
      }

      var blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'fiche_info.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  function initEditing() {
    if (!UploadModule.EDITING) return;
    var d = UploadModule.getEditData();
    var typeSelect = document.getElementById('type');
    var formatTypeSelect = document.getElementById('format_type');

    document.getElementById('title').value = d.title || '';
    if (typeSelect && d.type) {
      typeSelect.value = d.type;
      typeSelect.dispatchEvent(new Event('change'));
      if (formatTypeSelect) formatTypeSelect.value = d.format_type || '';
    }
    document.getElementById('description').value = d.description || '';
    if (d.organization_id) document.getElementById('organization_id').value = d.organization_id;
    if (d.license_type) {
      var lt = document.getElementById('license_type');
      lt.value = d.license_type;
      lt.dispatchEvent(new Event('change'));
    }
    uploadBtn.textContent = 'Mettre \u00e0 jour et publier';
    draftBtn.textContent = 'Mettre \u00e0 jour le brouillon';
    var h1 = document.querySelector('.upload-header h1');
    if (h1) h1.textContent = 'Modifier un brouillon';
  }

  function init() {
    UploadModule.formControls.init();
    UploadModule.dataInput.init();
    UploadModule.magnets.init();
    UploadModule.imageMagnets.init();
    UploadModule.tabs.init();
    UploadModule.history.init();
    initFormSubmission();
    initDraftBtn();
    initDownloadJson();
    initEditing();
  }

  return { init: init };
})();

UploadModule.submit.init();