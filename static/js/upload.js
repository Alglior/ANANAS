document.addEventListener('DOMContentLoaded', function() {
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

    if (!isNonData()) {
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

    showSpinner('Envoi des données...', 'Étape 1/2');

    var csrfToken = CsrfModule.getCsrfToken();

    try {
      var chunkId = null;
      if (!isNonData()) {
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

        var fileResp = await fetch('/api/upload/file', {
          method: 'POST',
          headers: { 'X-CSRF-Token': csrfToken },
          body: formData,
        });
        var fileData = await fileResp.json();
        if (!fileResp.ok) {
          hideSpinner();
          uploadStatus.textContent = fileData.error || 'Erreur téléversement';
          uploadStatus.className = 'form-status form-error';
          uploadBtn.disabled = false;
          if (draftBtn) draftBtn.disabled = false;
          return;
        }
        chunkId = fileData.chunk_id;
      }

      showSpinner('Création de l\'item...', 'Étape 2/2');

      var itemPayload = buildItemPayload(magnetLinks, false);
      if (chunkId) itemPayload.chunk_id = chunkId;

      var itemResp = await fetch('/api/upload/item', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        body: JSON.stringify(itemPayload),
      });
      var itemData = await itemResp.json();

      if (!itemResp.ok) {
        hideSpinner();
        uploadStatus.textContent = itemData.error || 'Erreur création de l\'item';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        return;
      }

      var hasImages = itemPayload.image_magnets && itemPayload.image_magnets.length > 0;
      if (hasImages) {
        showSpinner('Publication réussie !', 'Téléchargement des images en arrière-plan...', true);
        setTimeout(function() {
          window.location.href = '/catalogue/item/' + itemData.id;
        }, 2000);
      } else {
        showSpinner('Publication réussie !', 'Redirection...');
        setTimeout(function() {
          window.location.href = '/catalogue/item/' + itemData.id;
        }, 1500);
      }

    } catch (err) {
      hideSpinner();
      uploadStatus.textContent = 'Erreur de communication';
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

      showSpinner('Enregistrement du brouillon...', '');

      var payload = buildItemPayload([], true);
      payload.status = 'draft';

      var csrfToken = CsrfModule.getCsrfToken();

      try {
        var response = await fetch('/api/upload/item', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken,
          },
          body: JSON.stringify(payload),
        });
        var data = await response.json();
        if (response.ok) {
          hideSpinner();
          window.location.href = '/catalogue/item/' + data.id;
        } else {
          hideSpinner();
          uploadStatus.textContent = data.error || 'Erreur';
          uploadStatus.className = 'form-status form-error';
        }
      } catch (err) {
        hideSpinner();
        uploadStatus.textContent = 'Erreur réseau';
        uploadStatus.className = 'form-status form-error';
      }
    });
  }

  if (typeSelect) {
    populateFormats(typeSelect.value);
  }

  createMagnetEntry('', 'regions');
});
