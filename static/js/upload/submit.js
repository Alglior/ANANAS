/**
 * A.N.A.N.A.S — Upload : submit, draft, JSON download, EDITING prefill
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

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
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

    showSpinner(UploadModule.EDITING ? 'Mise \u00e0 jour en cours...' : 'Envoi des donn\u00e9es...', UploadModule.EDITING ? '' : '\u00c9tape 1/2');

    var csrfToken = CsrfModule.getCsrfToken();

    try {
      var chunkId = null;
      if (!UploadModule.EDITING && !isNonData) {
        var dataTextValue = dataInput.value;
        var dataLines = dataTextValue.split('\n').filter(function(line) { return line.trim(); }).slice(0, 50);
        if (dataLines.length) {
          var formData = new FormData();
          formData.append('data_text', dataLines.join('\n'));
          formData.append('title', title);
          formData.append('type', typeSelect.value);
          formData.append('format_type', document.getElementById('format_type').value);
          formData.append('description', document.getElementById('description').value.trim());
          var dataFormatLevelRadio = document.querySelector('input[name="data_format_level"]:checked');
          formData.append('data_format_level', dataFormatLevelRadio ? dataFormatLevelRadio.value : 'pack');

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

  function populateFormFromJSON(d) {
    var typeSelect = document.getElementById('type');
    var formatTypeSelect = document.getElementById('format_type');

    document.getElementById('title').value = d.title || '';
    if (typeSelect && d.type) {
      typeSelect.value = d.type;
      typeSelect.dispatchEvent(new Event('change'));
      if (formatTypeSelect) formatTypeSelect.value = d.format_type || '';
    }
    document.getElementById('description').value = d.description || '';
    var tagsInput = document.getElementById('tags');
    if (tagsInput && d.tags && d.tags.length > 0) {
      tagsInput.value = d.tags.join(', ');
    }
    if (d.organization_id) document.getElementById('organization_id').value = d.organization_id;
    if (d.license_type) {
      var lt = document.getElementById('license_type');
      lt.value = d.license_type;
      lt.dispatchEvent(new Event('change'));
      if (d.license_type === 'other' && d.custom_license_text) {
        document.getElementById('custom_license_text').value = d.custom_license_text;
      }
    }

    // Restore data format level
    if (d.data_format_level) {
      var radio = document.querySelector('input[name="data_format_level"][value="' + d.data_format_level + '"]');
      if (radio) radio.checked = true;
    }

    // Restore magnet links
    if (d.data_format_level === 'simple' || d.data_format_level === 'pack') {
      var magnetEntries = document.getElementById('magnetEntries');
      if (magnetEntries) {
        magnetEntries.innerHTML = '';
        if (d.data_format_level === 'pack' && d.metadata_json && d.metadata_json.zoom_levels) {
          UploadModule.magnets.createEntry(d.magnet_link, d.metadata_json.zoom_levels.join(','));
        } else {
          UploadModule.magnets.createEntry(d.magnet_link, 'regions');
        }
        if (d.data_format_level === 'pack') {
          UploadModule.magnets.setSingleEntryMode(true, true);
        } else if (d.data_format_level === 'simple') {
          UploadModule.magnets.setSingleEntryMode(true, false);
        }
      }
    } else if (d.data_format_level === 'individual' && d.magnet_links && d.magnet_links.length > 0) {
      var magnetEntries = document.getElementById('magnetEntries');
      if (magnetEntries) {
        magnetEntries.innerHTML = '';
        d.magnet_links.forEach(function(ml) {
          UploadModule.magnets.createEntry(ml.magnet_link || '', ml.zoom_level || 'regions');
        });
      }
    }

    // Restore PDF magnet
    var pdfInput = document.getElementById('pdf_magnet_link');
    if (pdfInput && d.pdf_magnet_link) {
      pdfInput.value = d.pdf_magnet_link;
    }

    // Restore visualization links (supports both formats)
    if (d.visualization_links && d.visualization_links.length > 0) {
      var vln = document.getElementById('viz_name');
      var vlu = document.getElementById('viz_url');
      if (vln && vlu) {
        vln.value = d.visualization_links[0].name || '';
        vlu.value = d.visualization_links[0].url || '';
      }
    } else if (d.viz_link_name || d.viz_link_url) {
      var vln = document.getElementById('viz_name');
      var vlu = document.getElementById('viz_url');
      if (vln) vln.value = d.viz_link_name || '';
      if (vlu) vlu.value = d.viz_link_url || '';
    }

    // Restore image magnets
    if (d.image_magnets && d.image_magnets.length > 0) {
      var imageContainer = document.getElementById('imageMagnetEntries');
      if (imageContainer) {
        imageContainer.innerHTML = '';
        d.image_magnets.forEach(function(im) {
          UploadModule.imageMagnets.createEntry(im.magnet_link || '', im.label || '');
        });
      }
    }

    // Restore data text for preview
    if (d.data_text) {
      var dataInput = document.getElementById('data_input');
      if (dataInput) {
        dataInput.value = d.data_text;
        dataInput.dispatchEvent(new Event('input'));
      }
    }
  }

  function initMultiJsonUpload() {
    var dropZone = document.getElementById('jsonDropZone');
    var fileInput = document.getElementById('multiJsonInput');
    var resultsContainer = document.getElementById('jsonUploadResults');
    if (!dropZone || !fileInput) return;

    function processFiles(files) {
      var validFiles = [];
      for (var i = 0; i < files.length; i++) {
        var f = files[i];
        if (f.name.endsWith('.json')) {
          validFiles.push(f);
        }
      }
      if (!validFiles.length) {
        uploadStatus.textContent = 'Aucun fichier JSON valide s\u00e9lectionn\u00e9';
        uploadStatus.className = 'form-status form-error';
        return;
      }

      // Si 1 seul fichier JSON : remplir le formulaire au lieu de créer directement
      if (validFiles.length === 1) {
        var reader = new FileReader();
        reader.onload = function(ev) {
          try {
            var data = JSON.parse(ev.target.result);
            if (!data.title && !data.type) {
              throw new Error('Champs title/type manquants');
            }
            populateFormFromJSON(data);
            resultsContainer.innerHTML = '<div class="json-upload-result success"><span class="status-icon"></span><span class="file-name">' + escapeHtml(validFiles[0].name) + '</span><span class="file-status">Formulaire rempli \u2014 vérifiez puis enregistrez</span></div>';
          } catch (err) {
            resultsContainer.innerHTML = '<div class="json-upload-result error"><span class="status-icon"></span><span class="file-name">' + escapeHtml(validFiles[0].name) + '</span><span class="file-status">JSON invalide: ' + escapeHtml(err.message) + '</span></div>';
          }
        };
        reader.readAsText(validFiles[0]);
        return;
      }

      // Sinon : batch create via API
      resultsContainer.innerHTML = '';
      var total = validFiles.length;
      var done = 0;

      validFiles.forEach(function(file) {
        var row = document.createElement('div');
        row.className = 'json-upload-result';
        row.innerHTML = '<span class="status-icon"></span><span class="file-name">' + escapeHtml(file.name) + '</span><span class="file-status">Envoi...</span>';
        resultsContainer.appendChild(row);

        var reader = new FileReader();
        reader.onload = function(ev) {
          try {
            var data = JSON.parse(ev.target.result);
            if (!data.title && !data.type) {
              throw new Error('Champs title/type manquants');
            }
            var payload = {
              title: data.title || '',
              type: data.type || '',
              format_type: data.format_type || '',
              description: data.description || '',
              organization_id: data.organization_id || '',
              license_type: data.license_type || '',
              custom_license_text: data.custom_license_text || '',
              pdf_magnet_link: data.pdf_magnet_link || '',
              status: 'draft'
            };
            if (data.tags && data.tags.length > 0) {
              payload.tags = data.tags;
            }
            if (data.data_format_level === 'simple' && data.magnet_link) {
              payload.data_format_level = 'simple';
              payload.magnet_link = data.magnet_link;
            } else if (data.data_format_level === 'pack' && data.magnet_link) {
              payload.data_format_level = 'pack';
              payload.magnet_link = data.magnet_link;
            } else if (data.data_format_level === 'individual' && data.magnet_links && data.magnet_links.length > 0) {
              payload.data_format_level = 'individual';
              payload.magnet_links = data.magnet_links;
            }
            if (data.viz_link_name || data.viz_link_url) {
              payload.viz_link_name = data.viz_link_name || '';
              payload.viz_link_url = data.viz_link_url || '';
            }
            if (data.image_magnets && data.image_magnets.length > 0) {
              payload.image_magnets = data.image_magnets;
            }

            var csrfToken = CsrfModule.getCsrfToken();
            
            // Upload data_text first if present
            function uploadDataAndCreateItem() {
              if (data.data_text && data.data_text.trim()) {
                var formData = new FormData();
                formData.append('data_text', data.data_text);
                formData.append('title', payload.title);
                formData.append('type', payload.type);
                formData.append('format_type', payload.format_type);
                formData.append('description', payload.description);
                formData.append('organization_id', payload.organization_id || '');
                
                return fetch('/api/upload/file', {
                  method: 'POST',
                  headers: { 'X-CSRF-Token': csrfToken },
                  body: formData,
                })
                .then(function(resp) { return resp.json(); })
                .then(function(result) {
                  if (result.chunk_id) {
                    payload.chunk_id = result.chunk_id;
                  }
                  return payload;
                })
                .catch(function() { return payload; });
              }
              return Promise.resolve(payload);
            }
            
            uploadDataAndCreateItem().then(function(finalPayload) {
              return fetch('/api/upload/item', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRF-Token': csrfToken,
                },
                body: JSON.stringify(finalPayload),
              })
              .then(function(resp) {
                if (!resp.ok) {
                  return resp.json().then(function(d) { throw new Error(d.error || 'Erreur serveur'); });
                }
                return resp.json();
              })
              .then(function() {
                row.className = 'json-upload-result success';
                row.innerHTML = '<span class="status-icon"></span><span class="file-name">' + escapeHtml(file.name) + '</span><span class="file-status">Brouillon cr\u00e9\u00e9</span>';
              })
              .catch(function(err) {
                row.className = 'json-upload-result error';
                row.innerHTML = '<span class="status-icon"></span><span class="file-name">' + escapeHtml(file.name) + '</span><span class="file-status">' + escapeHtml(err.message) + '</span>';
              })
              .finally(function() {
                done++;
                if (done >= total) {
                  setTimeout(function() { location.reload(); }, 1500);
                }
              });
            });
          } catch (err) {
            row.className = 'json-upload-result error';
            row.innerHTML = '<span class="status-icon"></span><span class="file-name">' + escapeHtml(file.name) + '</span><span class="file-status">JSON invalide</span>';
            done++;
            if (done >= total) {
              setTimeout(function() { location.reload(); }, 1500);
            }
          }
        };
        reader.readAsText(file);
      });
    }

    dropZone.addEventListener('click', function() {
      fileInput.click();
    });

    fileInput.addEventListener('change', function(e) {
      processFiles(e.target.files);
      fileInput.value = '';
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
      dropZone.addEventListener(eventName, function(e) {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    dropZone.addEventListener('dragenter', function() {
      dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', function(e) {
      if (!dropZone.contains(e.relatedTarget)) {
        dropZone.classList.remove('drag-over');
      }
    });

    dropZone.addEventListener('drop', function(e) {
      dropZone.classList.remove('drag-over');
      processFiles(e.dataTransfer.files);
    });
  }

  function initEditing() {
    if (!UploadModule.EDITING) return;
    var d = UploadModule.getEditData();
    populateFormFromJSON(d);

    uploadBtn.textContent = 'Mettre \u00e0 jour et publier';
    draftBtn.textContent = 'Mettre \u00e0 jour le brouillon';
    var h1 = document.querySelector('.upload-header h1');
    if (h1) {
      if (d.status === 'published') {
        h1.textContent = 'Modifier la publication';
      } else {
        h1.textContent = 'Modifier un brouillon';
      }
    }
  }

  function init() {
    UploadModule.formControls.init();
    UploadModule.dataInput.init();
    UploadModule.magnets.init();
    UploadModule.imageMagnets.init();
    UploadModule.tabs.init();
    UploadModule.history.init();
    if (UploadModule.tagSelector) UploadModule.tagSelector.init();
    if (UploadModule.copyScript) UploadModule.copyScript.init();
    if (UploadModule.videoModal) UploadModule.videoModal.init();
    initFormSubmission();
    initDraftBtn();
    initDownloadJson();
    initMultiJsonUpload();
    initEditing();
  }

  return { init: init };
})();

UploadModule.submit.init();