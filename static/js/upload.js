document.addEventListener('DOMContentLoaded', function() {
  var EDITING = !!window.EDIT_DATA;
  var EDIT_ITEM_ID = EDITING ? window.EDIT_DATA.id : null;

  var tabs = document.querySelectorAll('.upload-tab');
  var tabContents = document.querySelectorAll('.upload-tab-content');
  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      var target = this.getAttribute('data-tab');
      tabs.forEach(function(t) { t.classList.remove('active'); });
      tabContents.forEach(function(c) { c.classList.remove('active'); });
      this.classList.add('active');
      var content = document.getElementById('tab-' + target);
      if (content) content.classList.add('active');
    });
  });

  if (window.location.search.indexOf('drafts=1') !== -1) {
    var draftsTab = document.querySelector('.upload-tab[data-tab="drafts"]');
    if (draftsTab) draftsTab.click();
  }

  var dataInput = document.getElementById('data_input');
  var dataLineCount = document.getElementById('dataLineCount');
  var MAX_LINES = 50;

  if (dataInput) {
    function updateLineCount() {
      var lines = dataInput.value.split('\n').filter(function(line) { return line.trim(); });
      var count = Math.min(lines.length, MAX_LINES);
      dataLineCount.textContent = count + ' ligne(s) / ' + MAX_LINES + ' max';
      if (lines.length > MAX_LINES) {
        dataLineCount.classList.add('color-error');
      } else {
        dataLineCount.classList.remove('color-error');
      }
    }

    dataInput.addEventListener('input', updateLineCount);
    dataInput.addEventListener('change', updateLineCount);
    updateLineCount();

    dataInput.addEventListener('paste', function(e) {
      setTimeout(function() {
        var lines = dataInput.value.split('\n').filter(function(line) { return line.trim(); });
        if (lines.length > MAX_LINES) {
          e.preventDefault();
          alert('Attention : vous avez collé ' + lines.length + ' lignes. Seules les ' + MAX_LINES + ' premières seront conservées.');
          dataInput.value = lines.slice(0, MAX_LINES).join('\n');
          updateLineCount();
        }
      }, 10);
    });
  }

  var uploadForm = document.getElementById('uploadForm');
  var uploadBtn = document.getElementById('uploadBtn');
  var draftBtn = document.getElementById('draftBtn');
  var uploadStatus = document.getElementById('uploadStatus');
  var typeSelect = document.getElementById('type');
  var formatTypeSelect = document.getElementById('format_type');
  var dataTextInputGroup = document.getElementById('dataTextInputGroup');
  var magnetEntries = document.getElementById('magnetEntries');
  var addMagnetBtn = document.getElementById('addMagnetBtn');
  var bulkMagnetBtn = document.getElementById('bulkMagnetBtn');
  var bulkMagnetGroup = document.getElementById('bulkMagnetGroup');
  var bulkZoomPills = document.getElementById('bulkZoomPills');
  var bulkMagnetTextarea = document.getElementById('bulkMagnetTextarea');
  var bulkMagnetCount = document.getElementById('bulkMagnetCount');
  var bulkMagnetConfirm = document.getElementById('bulkMagnetConfirm');
  var bulkMagnetCancel = document.getElementById('bulkMagnetCancel');
  var licenseTypeSelect = document.getElementById('license_type');
  var licenseOtherGroup = document.getElementById('licenseOtherGroup');
  var customLicenseText = document.getElementById('custom_license_text');
  var magnetActions = document.querySelector('#magnetSection .magnet-actions');

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

  if (licenseTypeSelect) {
    licenseTypeSelect.addEventListener('change', function() {
      if (licenseOtherGroup && customLicenseText) {
        if (this.value === 'other') {
          licenseOtherGroup.classList.remove('hidden-section');
          customLicenseText.required = true;
        } else {
          licenseOtherGroup.classList.add('hidden-section');
          customLicenseText.required = false;
          customLicenseText.value = '';
        }
      }
    });
  }

  var formatDict = {
    geodonnee: [
      { value: 'geopackage', label: 'Geopackage (.gpkg)' },
      { value: 'csv', label: 'CSV' },
      { value: 'shp', label: 'Shapefile (.shp)' },
      { value: 'geojson', label: 'GeoJSON' },
      { value: 'kml', label: 'KML' },
      { value: 'gml', label: 'GML' },
      { value: 'gpx', label: 'GPX' },
      { value: 'topojson', label: 'TopoJSON' },
      { value: 'geoparquet', label: 'GeoParquet' },
      { value: 'tab', label: 'MapInfo TAB' },
      { value: 'xml', label: 'XML' }
    ],
    carte: [
      { value: 'png', label: 'PNG' },
      { value: 'jpg', label: 'JPG/JPEG' },
      { value: 'tiff', label: 'TIFF' },
      { value: 'gif', label: 'GIF' },
      { value: 'bmp', label: 'BMP' },
      { value: 'webp', label: 'WebP' }
    ],
    application: [
      { value: 'python', label: 'Python (.py)' },
      { value: 'rust', label: 'Rust (.rs)' },
      { value: 'javascript', label: 'JavaScript (.js)' },
      { value: 'typescript', label: 'TypeScript (.ts)' },
      { value: 'java', label: 'Java (.java)' },
      { value: 'go', label: 'Go (.go)' },
      { value: 'cpp', label: 'C++ (.cpp/.h)' },
      { value: 'html', label: 'HTML/CSS' }
    ]
  };

  function populateFormats(type) {
    if (!formatTypeSelect || !formatDict[type]) return;
    formatTypeSelect.innerHTML = '';
    formatDict[type].forEach(function(opt) {
      var option = document.createElement('option');
      option.value = opt.value;
      option.textContent = opt.label;
      formatTypeSelect.appendChild(option);
    });
  }

  function isNonData() {
    return typeSelect && (typeSelect.value === 'carte' || typeSelect.value === 'application');
  }

  if (typeSelect) {
    typeSelect.addEventListener('change', function() {
      populateFormats(this.value);
      if (dataTextInputGroup) {
        if (isNonData()) {
          dataTextInputGroup.classList.add('hidden-section');
        } else {
          dataTextInputGroup.classList.remove('hidden-section');
        }
      }
      if (magnetActions) {
        if (isNonData()) {
          magnetActions.classList.add('hidden-section');
        } else {
          magnetActions.classList.remove('hidden-section');
        }
      }
    });
  }

  function createMagnetEntry(magnetValue, zoomValue) {
    var entry = document.createElement('div');
    entry.className = 'magnet-entry';

    var row = document.createElement('div');
    row.className = 'magnet-entry-row';

    var magnetInput = document.createElement('input');
    magnetInput.type = 'text';
    magnetInput.name = 'magnet_link[]';
    magnetInput.placeholder = 'magnet:?xt=urn:btih:...';
    magnetInput.className = 'form-control';
    magnetInput.value = magnetValue || '';

    var removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-outline';
    removeBtn.textContent = '✕';
    removeBtn.addEventListener('click', function() {
      var allEntries = magnetEntries.querySelectorAll('.magnet-entry');
      if (allEntries.length <= 1) return;
      entry.remove();
    });

    row.appendChild(magnetInput);
    row.appendChild(removeBtn);

    var pills = document.createElement('div');
    pills.className = 'zoom-pills';

    var zoomInput = document.createElement('input');
    zoomInput.type = 'hidden';
    zoomInput.name = 'zoom_level[]';
    zoomInput.value = zoomValue || 'regions';

    var zoomLevels = ['iris', 'communes', 'departements', 'regions', 'pays'];
    var zoomLabels = ['IRIS', 'Communes', 'Départements', 'Régions', 'Pays'];

    zoomLevels.forEach(function(z, i) {
      var pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'zoom-pill';
      pill.setAttribute('data-zoom', z);
      pill.textContent = zoomLabels[i];
      if (z === (zoomValue || 'regions')) {
        pill.classList.add('active');
      }
      pills.appendChild(pill);
    });

    entry.appendChild(row);
    entry.appendChild(pills);
    entry.appendChild(zoomInput);
    magnetEntries.appendChild(entry);
  }

  magnetEntries.addEventListener('click', function(e) {
    var pill = e.target.closest('.zoom-pill');
    if (!pill) return;
    var entry = pill.closest('.magnet-entry');
    if (!entry) return;
    entry.querySelectorAll('.zoom-pill').forEach(function(p) { p.classList.remove('active'); });
    pill.classList.add('active');
    var hidden = entry.querySelector('input[name="zoom_level[]"]');
    if (hidden) {
      hidden.value = pill.getAttribute('data-zoom');
    }
  });

  if (addMagnetBtn) {
    addMagnetBtn.addEventListener('click', function() {
      createMagnetEntry('', 'regions');
    });
  }

  if (bulkZoomPills) {
    bulkZoomPills.addEventListener('click', function(e) {
      var pill = e.target.closest('.zoom-pill');
      if (!pill) return;
      bulkZoomPills.querySelectorAll('.zoom-pill').forEach(function(p) { p.classList.remove('active'); });
      pill.classList.add('active');
    });
  }

  if (bulkMagnetBtn) {
    bulkMagnetBtn.addEventListener('click', function() {
      if (bulkMagnetGroup.classList.contains('hidden-section')) {
        bulkMagnetGroup.classList.remove('hidden-section');
      } else {
        bulkMagnetGroup.classList.add('hidden-section');
      }
    });
  }

  if (bulkMagnetTextarea) {
    bulkMagnetTextarea.addEventListener('input', function() {
      var lines = bulkMagnetTextarea.value.split('\n').filter(function(l) { return l.trim(); });
      bulkMagnetCount.textContent = lines.length + ' liens détectés';
      bulkMagnetConfirm.textContent = 'Ajouter ces ' + lines.length + ' liens';
    });
  }

  if (bulkMagnetConfirm) {
    bulkMagnetConfirm.addEventListener('click', function() {
      var lines = bulkMagnetTextarea.value.split('\n').filter(function(l) { return l.trim(); });
      var activeZoom = bulkZoomPills.querySelector('.zoom-pill.active');
      var zoom = activeZoom ? activeZoom.getAttribute('data-zoom') : 'regions';
      lines.forEach(function(line) {
        createMagnetEntry(line.trim(), zoom);
      });
      bulkMagnetTextarea.value = '';
      bulkMagnetCount.textContent = '0 liens détectés';
      bulkMagnetConfirm.textContent = 'Ajouter ces X liens';
      bulkMagnetGroup.classList.add('hidden-section');
    });
  }

  if (bulkMagnetCancel) {
    bulkMagnetCancel.addEventListener('click', function() {
      bulkMagnetTextarea.value = '';
      bulkMagnetCount.textContent = '0 liens détectés';
      bulkMagnetConfirm.textContent = 'Ajouter ces X liens';
      bulkMagnetGroup.classList.add('hidden-section');
    });
  }

  function createImageEntry(magnetValue, labelValue) {
    var entry = document.createElement('div');
    entry.className = 'image-magnet-entry';

    var magnetInput = document.createElement('input');
    magnetInput.type = 'text';
    magnetInput.name = 'image_magnet_link[]';
    magnetInput.placeholder = 'magnet:?xt=urn:btih:...';
    magnetInput.className = 'form-control flex-3';
    magnetInput.value = magnetValue || '';

    var labelInput = document.createElement('input');
    labelInput.type = 'text';
    labelInput.name = 'image_label[]';
    labelInput.placeholder = 'Nom de l\'image (ex: Carte 2024)';
    labelInput.className = 'form-control flex-2';
    labelInput.value = labelValue || '';

    var removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-outline';
    removeBtn.textContent = '✕';
    removeBtn.addEventListener('click', function() { entry.remove(); });

    entry.appendChild(magnetInput);
    entry.appendChild(labelInput);
    entry.appendChild(removeBtn);
    document.getElementById('imageMagnetEntries').appendChild(entry);
  }

  var addImageMagnetBtn = document.getElementById('addImageMagnetBtn');
  if (addImageMagnetBtn) {
    addImageMagnetBtn.addEventListener('click', function() {
      createImageEntry('', '');
    });
  }

  var bulkImageMagnetBtn = document.getElementById('bulkImageMagnetBtn');
  if (bulkImageMagnetBtn) {
    bulkImageMagnetBtn.addEventListener('click', function() {
      var group = document.getElementById('bulkImageMagnetGroup');
      if (group.classList.contains('hidden-section')) {
        group.classList.remove('hidden-section');
      } else {
        group.classList.add('hidden-section');
      }
    });
  }

  var bulkImageTextarea = document.getElementById('bulkImageTextarea');
  var bulkImageCount = document.getElementById('bulkImageCount');
  if (bulkImageTextarea) {
    bulkImageTextarea.addEventListener('input', function() {
      var lines = bulkImageTextarea.value.split('\n').filter(function(l) { return l.trim(); });
      bulkImageCount.textContent = lines.length + ' liens détectés';
      document.getElementById('bulkImageConfirm').textContent = 'Ajouter ces ' + lines.length + ' liens';
    });
  }

  var bulkImageConfirm = document.getElementById('bulkImageConfirm');
  if (bulkImageConfirm) {
    bulkImageConfirm.addEventListener('click', function() {
      var lines = bulkImageTextarea.value.split('\n').filter(function(l) { return l.trim(); });
      lines.forEach(function(line) {
        createImageEntry(line.trim(), '');
      });
      bulkImageTextarea.value = '';
      bulkImageCount.textContent = '0 liens détectés';
      bulkImageConfirm.textContent = 'Ajouter ces X liens';
      document.getElementById('bulkImageMagnetGroup').classList.add('hidden-section');
    });
  }

  var bulkImageCancel = document.getElementById('bulkImageCancel');
  if (bulkImageCancel) {
    bulkImageCancel.addEventListener('click', function() {
      bulkImageTextarea.value = '';
      bulkImageCount.textContent = '0 liens détectés';
      bulkImageConfirm.textContent = 'Ajouter ces X liens';
      document.getElementById('bulkImageMagnetGroup').classList.add('hidden-section');
    });
  }

  function collectMagnetLinks() {
    var entries = magnetEntries.querySelectorAll('.magnet-entry');
    var links = [];
    entries.forEach(function(entry) {
      var input = entry.querySelector('input[type="text"]');
      var hidden = entry.querySelector('input[name="zoom_level[]"]');
      var val = input ? input.value.trim() : '';
      if (val) {
        links.push({
          magnet_link: val,
          zoom_level: hidden ? hidden.value : 'regions',
        });
      }
    });
    return links;
  }

  function collectImageMagnets() {
    var entries = document.querySelectorAll('#imageMagnetEntries .image-magnet-entry');
    var images = [];
    entries.forEach(function(entry) {
      var magnetInput = entry.querySelector('input[name="image_magnet_link[]"]');
      var labelInput = entry.querySelector('input[name="image_label[]"]');
      var magnet = magnetInput ? magnetInput.value.trim() : '';
      if (magnet) {
        images.push({
          magnet_link: magnet,
          label: labelInput ? labelInput.value.trim() : '',
        });
      }
    });
    return images;
  }

  function buildItemPayload(magnetLinks, isDraft) {
    var payload = {
      title: document.getElementById('title').value.trim(),
      type: typeSelect.value,
      format_type: formatTypeSelect.value,
      description: document.getElementById('description').value.trim(),
      organization_id: document.getElementById('organization_id').value || '',
      license_type: document.getElementById('license_type').value || '',
      custom_license_text: document.getElementById('custom_license_text').value || '',
    };

    if (isDraft) {
      payload.status = 'draft';
    }

    if (!isDraft) {
      if (magnetLinks.length === 1) {
        payload.data_format_level = 'pack';
        payload.magnet_link = magnetLinks[0].magnet_link;
      } else if (magnetLinks.length > 1) {
        payload.data_format_level = 'individual';
        payload.magnet_links = magnetLinks;
      }
    }

    var vizName = document.getElementById('viz_name');
    var vizUrl = document.getElementById('viz_url');
    if (vizName.value && vizUrl.value) {
      payload.viz_link_name = vizName.value.trim();
      payload.viz_link_url = vizUrl.value.trim();
    }

    var imageMagnets = collectImageMagnets();
    if (imageMagnets.length > 0) {
      payload.image_magnets = imageMagnets;
    }

    return payload;
  }

  async function safeFetchJson(url, options) {
    var resp = await fetch(url, options);
    var contentType = resp.headers.get('content-type') || '';
    if (resp.redirected) {
      throw new Error('SESSION_EXPIRED');
    }
    if (!contentType.includes('application/json')) {
      var text = await resp.text();
      console.error('Réponse non-JSON de ' + url + ' (status ' + resp.status + '):', text.substring(0, 300));
      throw new Error('NON_JSON_RESPONSE');
    }
    var data = await resp.json();
    return { response: resp, data: data };
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var magnetLinks = collectMagnetLinks();
      submitPublish(magnetLinks);
    });
  }

  async function submitPublish(magnetLinks) {
    var selectedType = typeSelect ? typeSelect.value : '';
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

    if (!isNonData()) {
      var magnetLinksFilled = magnetLinks.filter(function(l) { return l.magnet_link; });
      if (!magnetLinksFilled.length) {
        uploadStatus.textContent = 'Au moins un lien Magnet est requis';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        return;
      }
    }

    if (!EDITING && !isNonData()) {
      var dataText = dataInput ? dataInput.value : '';
      var lines = dataText.split('\n').filter(function(line) { return line.trim(); }).slice(0, MAX_LINES);
      if (!lines.length) {
        uploadStatus.textContent = 'Veuillez coller vos données';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        return;
      }
    }

    showSpinner(EDITING ? 'Mise à jour en cours...' : 'Envoi des données...', EDITING ? '' : 'Étape 1/2');

    var csrfToken = CsrfModule.getCsrfToken();

    try {
      var chunkId = null;
      if (!EDITING && !isNonData()) {
        var formData = new FormData();
        var dataText = dataInput.value;
        var dataLines = dataText.split('\n').filter(function(line) { return line.trim(); }).slice(0, MAX_LINES);
        formData.append('data_text', dataLines.join('\n'));
        formData.append('title', title);
        formData.append('type', selectedType);
        formData.append('format_type', formatTypeSelect.value);
        formData.append('description', document.getElementById('description').value.trim());
        formData.append('data_format_level', 'pack');

        var orgId = document.getElementById('organization_id').value;
        if (orgId) formData.append('organization_id', orgId);
        var lt = document.getElementById('license_type');
        if (lt && lt.value) {
          formData.append('license_type', lt.value);
          if (lt.value === 'other') {
            formData.append('custom_license_text', customLicenseText.value);
          }
        }

        var fileResult = await safeFetchJson('/api/upload/file', {
          method: 'POST',
          headers: { 'X-CSRF-Token': csrfToken },
          body: formData,
        });
        if (!fileResult.response.ok) {
          hideSpinner();
          uploadStatus.textContent = fileResult.data.error || 'Erreur téléversement';
          uploadStatus.className = 'form-status form-error';
          uploadBtn.disabled = false;
          if (draftBtn) draftBtn.disabled = false;
          return;
        }
        chunkId = fileResult.data.chunk_id;
      }

      showSpinner(EDITING ? 'Publication du brouillon...' : 'Création de l\'item...', EDITING ? '' : 'Étape 2/2');

      var itemPayload = buildItemPayload(magnetLinks, false);
      if (chunkId) itemPayload.chunk_id = chunkId;

      var method = EDITING ? 'PUT' : 'POST';
      var url = EDITING ? '/api/upload/item/' + EDIT_ITEM_ID : '/api/upload/item';

      var itemResult = await safeFetchJson(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        body: JSON.stringify(itemPayload),
      });

      if (!itemResult.response.ok) {
        hideSpinner();
        uploadStatus.textContent = itemResult.data.error || 'Erreur création de l\'item';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        return;
      }

      var redirectId = itemResult.data.id || EDIT_ITEM_ID;
      var hasImages = itemPayload.image_magnets && itemPayload.image_magnets.length > 0;
      if (hasImages) {
        showSpinner('Publication réussie !', 'Téléchargement des images en arrière-plan...', true);
        setTimeout(function() {
          window.location.href = '/catalogue/item/' + redirectId;
        }, 2000);
      } else {
        showSpinner('Publication réussie !', 'Redirection...');
        setTimeout(function() {
          window.location.href = '/catalogue/item/' + redirectId;
        }, 1500);
      }

    } catch (err) {
      hideSpinner();
      if (err.message === 'SESSION_EXPIRED') {
        uploadStatus.textContent = 'Session expirée, veuillez vous reconnecter';
      } else {
        console.error('Erreur de communication:', err);
        uploadStatus.textContent = 'Erreur de communication';
      }
      uploadStatus.className = 'form-status form-error';
      uploadBtn.disabled = false;
      if (draftBtn) draftBtn.disabled = false;
    }
  }

  if (draftBtn) {
    draftBtn.addEventListener('click', async function() {
      var title = document.getElementById('title').value.trim();
      if (!title) {
        uploadStatus.textContent = 'Le titre est requis même pour un brouillon';
        uploadStatus.className = 'form-status form-error';
        return;
      }

      draftBtn.disabled = true;
      showSpinner('Enregistrement du brouillon...', '');

      var payload = buildItemPayload([], true);
      payload.status = 'draft';

      var csrfToken = CsrfModule.getCsrfToken();
      var method = EDITING ? 'PUT' : 'POST';
      var url = EDITING ? '/api/upload/item/' + EDIT_ITEM_ID : '/api/upload/item';

      try {
        var result = await safeFetchJson(url, {
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
          uploadStatus.textContent = 'Session expirée, veuillez vous reconnecter';
        } else if (err.message === 'NON_JSON_RESPONSE') {
          uploadStatus.textContent = 'Erreur serveur inattendue';
        } else {
          console.error('Erreur réseau:', err);
          uploadStatus.textContent = 'Erreur réseau';
        }
        uploadStatus.className = 'form-status form-error';
      }
    });
  }

  var downloadJsonBtn = document.getElementById('downloadJsonBtn');
  if (downloadJsonBtn) {
    downloadJsonBtn.addEventListener('click', function() {
      var magnetLinks = collectMagnetLinks();
      var payload = buildItemPayload(magnetLinks, false);

      var imageMagnets = collectImageMagnets();
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

  if (typeSelect) {
    populateFormats(typeSelect.value);
  }

  createMagnetEntry('', 'regions');

  if (EDITING) {
    var d = window.EDIT_DATA;
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
    uploadBtn.textContent = 'Mettre à jour et publier';
    draftBtn.textContent = 'Mettre à jour le brouillon';
    document.querySelector('.upload-header h1').textContent = 'Modifier un brouillon';
  }

  document.addEventListener('click', function(e) {
    var delBtn = e.target.closest('.draft-delete-btn');
    if (delBtn) {
      e.preventDefault();
      var draftId = delBtn.getAttribute('data-id');
      showConfirm(
        'Mettre ce brouillon à la corbeille ?<br><small>Il restera récupérable pendant 7 jours.</small>',
        function() { sendDelete('/api/upload/item/' + draftId, delBtn); }
      );
      return;
    }

    var restoreBtn = e.target.closest('.trash-restore-btn');
    if (restoreBtn) {
      e.preventDefault();
      var restoreId = restoreBtn.getAttribute('data-id');
      sendRestore('/api/upload/item/' + restoreId + '/restore', restoreBtn);
      return;
    }

    var purgeBtn = e.target.closest('.trash-purge-btn');
    if (purgeBtn) {
      e.preventDefault();
      var purgeId = purgeBtn.getAttribute('data-id');
      showConfirm(
        'Supprimer définitivement ce brouillon ?<br><small>Cette action est irréversible.</small>',
        function() { sendDelete('/api/upload/item/' + purgeId + '/purge', purgeBtn); }
      );
      return;
    }
  });

  function showConfirm(message, onConfirm) {
    var overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = [
      '<div class="confirm-dialog">',
      '<p>' + message + '</p>',
      '<div class="confirm-actions">',
      '<button class="btn-cancel">Annuler</button>',
      '<button class="btn-danger">Supprimer</button>',
      '</div>',
      '</div>'
    ].join('');
    document.body.appendChild(overlay);

    overlay.querySelector('.btn-cancel').addEventListener('click', function() {
      overlay.remove();
    });
    overlay.querySelector('.btn-danger').addEventListener('click', function() {
      overlay.remove();
      onConfirm();
    });
    overlay.addEventListener('click', function(ev) {
      if (ev.target === overlay) overlay.remove();
    });
  }

  function sendDelete(url, btn) {
    var csrfToken = CsrfModule.getCsrfToken();
    fetch(url, {
      method: 'DELETE',
      headers: { 'X-CSRF-Token': csrfToken },
    }).then(function(resp) {
      if (resp.ok) {
        window.location.reload();
      }
    });
  }

  function sendRestore(url, btn) {
    var csrfToken = CsrfModule.getCsrfToken();
    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    }).then(function(resp) {
      if (resp.ok) {
        window.location.reload();
      }
    });
  }

  var currentDraftPage = 1;
  var currentTrashPage = 1;

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderDraftItem(d) {
    return '<li class="upload-history-item" data-draft-id="' + d.id + '">' +
      '<a href="/catalogue/item/' + d.id + '" class="upload-history-link">' + escapeHtml(d.title) + '</a>' +
      '<span class="upload-history-meta">' +
        '<span class="badge badge-draft">Brouillon</span>' +
        ' ' + d.created_at +
        ' <a href="/upload?edit=' + d.id + '" class="btn btn-sm">Modifier</a>' +
        ' <button type="button" class="btn btn-sm btn-outline draft-delete-btn" data-id="' + d.id + '">Supprimer</button>' +
      '</span>' +
    '</li>';
  }

  function renderTrashItem(t) {
    return '<li class="upload-history-item" data-draft-id="' + t.id + '">' +
      '<span class="upload-history-link trashed-title">' + escapeHtml(t.title) + '</span>' +
      '<span class="upload-history-meta">' +
        '<span class="badge badge-trashed">Corbeille</span>' +
        ' ' + t.deleted_at +
        ' <button type="button" class="btn btn-sm btn-outline trash-restore-btn" data-id="' + t.id + '">Restaurer</button>' +
        ' <button type="button" class="btn btn-sm btn-outline trash-purge-btn" data-id="' + t.id + '">Supprimer</button>' +
      '</span>' +
    '</li>';
  }

  function renderPagination(data, containerId) {
    var container = document.getElementById(containerId);
    if (!container || data.total_pages <= 1) {
      if (container) container.innerHTML = '';
      return;
    }
    var html = '<nav class="pagination" aria-label="Pagination">';

    if (data.page > 1) {
      html += '<a class="btn btn-outline transition-hover pagination-prev" href="#" data-page="' + (data.page - 1) + '">&#9664;&nbsp;Précédent</a>';
    } else {
      html += '<span class="btn btn-outline pagination-prev disabled">&#9664;&nbsp;Précédent</span>';
    }

    html += '<div class="pagination-numbers">';
    for (var i = 0; i < data.page_numbers.length; i++) {
      var p = data.page_numbers[i];
      if (p === '...') {
        html += '<span class="pagination-ellipsis">&hellip;</span>';
      } else if (p === data.page) {
        html += '<span class="pagination-link active">' + p + '</span>';
      } else {
        html += '<a class="pagination-link" href="#" data-page="' + p + '">' + p + '</a>';
      }
    }
    html += '</div>';

    if (data.page < data.total_pages) {
      html += '<a class="btn btn-outline transition-hover pagination-next" href="#" data-page="' + (data.page + 1) + '">Suivant&nbsp;&#9658;</a>';
    } else {
      html += '<span class="btn btn-outline pagination-next disabled">Suivant&nbsp;&#9658;</span>';
    }

    html += '</nav>';
    container.innerHTML = html;
  }

  function loadDraftsPage(page) {
    currentDraftPage = page;
    var list = document.getElementById('drafts-list');
    var empty = document.getElementById('drafts-empty');
    if (!list && !empty) return;

    fetch('/api/upload/drafts?page=' + page, {
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
    }).then(function(resp) { return resp.json(); })
    .then(function(data) {
      if (data.total_items === 0 || data.drafts.length === 0) {
        if (list) list.style.display = 'none';
        if (!empty) {
          empty = document.createElement('p');
          empty.className = 'no-data-message';
          empty.id = 'drafts-empty';
          var tabDrafts = document.getElementById('tab-drafts');
          if (tabDrafts) tabDrafts.insertBefore(empty, document.getElementById('draft-pagination'));
        }
        empty.style.display = '';
        empty.textContent = 'Aucun brouillon pour le moment.';
      } else {
        if (empty) empty.style.display = 'none';
        if (!list) {
          list = document.createElement('ul');
          list.className = 'upload-history-list';
          list.id = 'drafts-list';
          var pagDiv = document.getElementById('draft-pagination');
          var tabDrafts = document.getElementById('tab-drafts');
          if (tabDrafts && pagDiv) tabDrafts.insertBefore(list, pagDiv);
        }
        list.style.display = '';
        list.innerHTML = data.drafts.map(renderDraftItem).join('');
      }
      renderPagination(data, 'draft-pagination');
    }).catch(function() {
      console.error('Failed to load drafts');
    });
  }

  function loadTrashPage(page) {
    currentTrashPage = page;
    var list = document.getElementById('trash-list');
    var empty = document.getElementById('trash-empty');

    fetch('/api/upload/trash?page=' + page, {
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
    }).then(function(resp) { return resp.json(); })
    .then(function(data) {
      if (data.total_items === 0 || data.trashed.length === 0) {
        if (list) list.style.display = 'none';
        if (!empty) {
          empty = document.createElement('p');
          empty.className = 'no-data-message';
          empty.id = 'trash-empty';
          var hint = document.querySelector('#tab-trash .trash-hint');
          var pagDiv = document.getElementById('trash-pagination');
          var tabTrash = document.getElementById('tab-trash');
          if (tabTrash && pagDiv) tabTrash.insertBefore(empty, pagDiv);
        }
        empty.style.display = '';
        empty.textContent = 'La corbeille est vide.';
      } else {
        if (empty) empty.style.display = 'none';
        if (!list) {
          list = document.createElement('ul');
          list.className = 'upload-history-list';
          list.id = 'trash-list';
          var hint = document.querySelector('#tab-trash .trash-hint');
          if (hint) hint.style.display = '';
          var pagDiv = document.getElementById('trash-pagination');
          var tabTrash = document.getElementById('tab-trash');
          if (tabTrash && pagDiv) tabTrash.insertBefore(list, pagDiv);
        }
        list.style.display = '';
        list.innerHTML = data.trashed.map(renderTrashItem).join('');
      }
      renderPagination(data, 'trash-pagination');
    }).catch(function() {
      console.error('Failed to load trash');
    });
  }

  document.getElementById('draft-pagination').addEventListener('click', function(e) {
    e.preventDefault();
    var link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
    if (!link) return;
    var page = parseInt(link.dataset.page);
    loadDraftsPage(page);
  });

  document.getElementById('trash-pagination').addEventListener('click', function(e) {
    e.preventDefault();
    var link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
    if (!link) return;
    var page = parseInt(link.dataset.page);
    loadTrashPage(page);
  });
});
