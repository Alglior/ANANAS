document.addEventListener('DOMContentLoaded', function() {
  const dataInput = document.getElementById('data_input');
  const dataLineCount = document.getElementById('dataLineCount');
  const MAX_LINES = 50;

  if (dataInput) {
    function updateLineCount() {
      const lines = dataInput.value.split('\n').filter(line => line.trim());
      const count = Math.min(lines.length, MAX_LINES);
      dataLineCount.textContent = `${count} ligne(s) / ${MAX_LINES} max`;
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
      setTimeout(() => {
        const lines = dataInput.value.split('\n').filter(line => line.trim());
        if (lines.length > MAX_LINES) {
          e.preventDefault();
          alert(`Attention : vous avez collé ${lines.length} lignes. Seules les ${MAX_LINES} premières seront conservées.`);
          dataInput.value = lines.slice(0, MAX_LINES).join('\n');
          updateLineCount();
        }
      }, 10);
    });
  }

  const uploadForm = document.getElementById('uploadForm');
  const uploadBtn = document.getElementById('uploadBtn');
  const uploadStatus = document.getElementById('uploadStatus');
  const uploadProgress = document.getElementById('uploadProgress');
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const typeSelect = document.getElementById('type');
  const formatTypeSelect = document.getElementById('format_type');
  const dataTextInputGroup = document.getElementById('dataTextInputGroup');
  const dataFormatLevel = document.getElementById('data_format_level');
  const packMagnetGroup = document.getElementById('packMagnetGroup');
  const individualMagnetGroup = document.getElementById('individualMagnetGroup');
  const magnetEntries = document.getElementById('magnetEntries');
  const addMagnetBtn = document.getElementById('addMagnetBtn');
  const licenseTypeSelect = document.getElementById('license_type');
  const licenseOtherGroup = document.getElementById('licenseOtherGroup');
  const customLicenseText = document.getElementById('custom_license_text');

  let magnetEntryCount = 0;

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

  const formatDict = {
    geodonnee: [
      { value: 'geopackage', label: 'Geopackage (.gpkg)' },
      { value: 'csv', label: 'CSV' },
      { value: 'shp', label: 'Shapefile (.shp)' },
      { value: 'geojson', label: 'GeoJSON' },
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
    formatDict[type].forEach(opt => {
      const option = document.createElement('option');
      option.value = opt.value;
      option.textContent = opt.label;
      formatTypeSelect.appendChild(option);
    });
  }

  if (typeSelect) {
    typeSelect.addEventListener('change', function() {
      populateFormats(this.value);
      if (dataTextInputGroup) {
        if (this.value === 'carte' || this.value === 'application') {
          dataTextInputGroup.classList.add('hidden-section');
        } else {
          dataTextInputGroup.classList.remove('hidden-section');
        }
      }
      if (dataFormatLevel) {
        if (this.value === 'application' || this.value === 'carte') {
          dataFormatLevel.closest('.form-group').classList.add('hidden-section');
        } else {
          dataFormatLevel.closest('.form-group').classList.remove('hidden-section');
        }
      }
    });
  }

  if (dataFormatLevel) {
    function toggleMagnetSections() {
      if (!packMagnetGroup || !individualMagnetGroup) return;
      packMagnetGroup.classList.remove('hidden-section');
      individualMagnetGroup.classList.remove('hidden-section');
      magnetEntries.innerHTML = '';
      magnetEntryCount = 0;
      if (this.value === 'pack') {
        // show pack, hide individual
        individualMagnetGroup.classList.add('hidden-section');
      } else {
        // show individual, hide pack
        packMagnetGroup.classList.add('hidden-section');
      }
    }
    dataFormatLevel.addEventListener('change', toggleMagnetSections);
    toggleMagnetSections.call({ value: dataFormatLevel.value });
  }

  if (addMagnetBtn) {
    addMagnetBtn.addEventListener('click', function() {
      const entry = document.createElement('div');
      entry.className = 'form-row magnet-entry magnet-entry-block';

      const magnetInput = document.createElement('input');
      magnetInput.type = 'text';
      magnetInput.name = 'magnet_link[]';
      magnetInput.placeholder = 'magnet:?xt=urn:btih:...';
      magnetInput.className = 'form-control flex-2';

      const zoomSelect = document.createElement('select');
      zoomSelect.name = 'zoom_level[]';
      zoomSelect.className = 'form-control flex-1';
      zoomSelect.innerHTML = `
        <option value="">-- Niveau de zoom --</option>
        <option value="iris">IRIS</option>
        <option value="communes">Communes</option>
        <option value="departements">Départements</option>
        <option value="regions">Régions</option>
        <option value="pays">Pays</option>
      `;

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'btn btn-outline flex-auto';
      removeBtn.textContent = 'Supprimer';
      removeBtn.addEventListener('click', () => { entry.remove(); });

      entry.appendChild(magnetInput);
      entry.appendChild(zoomSelect);
      entry.appendChild(removeBtn);
      magnetEntries.appendChild(entry);
      magnetEntryCount++;
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const selectedType = typeSelect ? typeSelect.value : '';
      uploadBtn.disabled = true;
      uploadStatus.textContent = 'Préparation...';
      uploadStatus.className = 'form-status';
      uploadProgress.classList.remove('hidden-section');

      if (selectedType !== 'carte' && selectedType !== 'application') {
        const dataText = dataInput ? dataInput.value : '';
        const lines = dataText.split('\n').filter(line => line.trim()).slice(0, MAX_LINES);

        if (!lines.length) {
          uploadStatus.textContent = 'Veuillez coller vos données';
          uploadStatus.className = 'form-status form-error';
          uploadBtn.disabled = false;
          uploadProgress.classList.add('hidden-section');
          return;
        }
      }

      const formData = new FormData();
      if (selectedType !== 'carte' && selectedType !== 'application') {
        const dataText = dataInput.value;
        const lines = dataText.split('\n').filter(line => line.trim()).slice(0, MAX_LINES);
        formData.append('data_text', lines.join('\n'));
      }
      formData.append('title', document.getElementById('title').value);
      formData.append('type', selectedType);
      formData.append('format_type', formatTypeSelect.value);
      formData.append('description', document.getElementById('description').value);
      if (selectedType === 'carte' || selectedType === 'application') {
        formData.append('data_format_level', 'pack');
      } else {
        formData.append('data_format_level', dataFormatLevel.value);
      }
      formData.append('organization_id', document.getElementById('organization_id').value);
      const licenseType = document.getElementById('license_type');
      if (licenseType && licenseType.value) {
        formData.append('license_type', licenseType.value);
        if (licenseType.value === 'other') {
          formData.append('custom_license_text', customLicenseText.value);
        }
      }

      let magnetLink = '';
      if (selectedType === 'carte' || selectedType === 'application' || dataFormatLevel.value === 'pack') {
        magnetLink = document.getElementById('magnet_link').value;
        if (!magnetLink) {
          uploadStatus.textContent = 'Le lien Magnet est requis';
          uploadStatus.className = 'form-status form-error';
          uploadBtn.disabled = false;
          uploadProgress.classList.add('hidden-section');
          return;
        }
        formData.append('magnet_link', magnetLink);
      } else {
        const entries = magnetEntries.querySelectorAll('.form-row');
        entries.forEach(entry => {
          const magnetInput = entry.querySelector('input[type="text"]');
          const zoomSelect = entry.querySelector('select');
          if (magnetInput && magnetInput.value) {
            formData.append('magnet_link[]', magnetInput.value);
            formData.append('zoom_level[]', zoomSelect ? zoomSelect.value : '');
          }
        });
      }

      // Add optional viz link
      const vizName = document.getElementById('viz_name');
      const vizUrl = document.getElementById('viz_url');
      if (vizName.value && vizUrl.value) {
        formData.append('viz_link_name', vizName.value);
        formData.append('viz_link_url', vizUrl.value);
      }

      try {
        const csrfToken = CsrfModule.getCsrfToken();
        const response = await fetch('/api/upload/file', {
          method: 'POST',
          headers: {
            'X-CSRF-Token': csrfToken,
          },
          body: formData,
        });

        const data = await response.json();

          if (!response.ok) {
            uploadStatus.textContent = data.error || 'Erreur téléversement';
            uploadStatus.className = 'form-status form-error';
            uploadBtn.disabled = false;
            uploadProgress.classList.add('hidden-section');
            return;
          }

          if (response.ok) {
            // Also create the item if not already created
          const itemPayload = {
            title: document.getElementById('title').value,
            type: selectedType,
            format_type: formatTypeSelect.value,
            description: document.getElementById('description').value,
            data_format_level: (selectedType === 'carte' || selectedType === 'application') ? 'pack' : dataFormatLevel.value,
            organization_id: document.getElementById('organization_id').value || '',
            chunk_id: data.chunk_id,
            license_type: document.getElementById('license_type').value || '',
            custom_license_text: document.getElementById('custom_license_text').value || '',
          };

          if (vizName.value && vizUrl.value) {
            itemPayload.viz_link_name = vizName.value;
            itemPayload.viz_link_url = vizUrl.value;
          }

          if (selectedType === 'carte' || selectedType === 'application' || dataFormatLevel.value === 'pack') {
            itemPayload.magnet_link = magnetLink;
          } else {
            const entries = magnetEntries.querySelectorAll('.form-row');
            itemPayload.magnet_links = [];
            entries.forEach(entry => {
              const magnetInput = entry.querySelector('input[type="text"]');
              const zoomSelect = entry.querySelector('select');
              if (magnetInput && magnetInput.value) {
                itemPayload.magnet_links.push({
                  magnet_link: magnetInput.value,
                  zoom_level: zoomSelect ? zoomSelect.value : '',
                });
              }
            });
          }

          const itemResponse = await fetch('/api/upload/item', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRF-Token': csrfToken,
            },
            body: JSON.stringify(itemPayload),
          });

          const itemData = await itemResponse.json();

          if (!itemResponse.ok) {
        uploadStatus.textContent = itemData.error || 'Erreur création de l\'item';
             uploadStatus.className = 'form-status form-error';
             uploadBtn.disabled = false;
             uploadProgress.classList.add('hidden-section');
             return;
          }

          progressBar.classList.add('progress-complete');
          progressBar.classList.remove('progress-error');
          progressText.textContent = 'Données publiées avec succès !';
          uploadStatus.textContent = 'Publication terminée';
          uploadStatus.className = 'form-status form-success';

          setTimeout(() => {
            window.location.href = '/catalogue/item/' + itemData.id;
          }, 1500);
        } else {
          progressBar.classList.remove('progress-complete');
          progressBar.classList.add('progress-error');
          progressText.textContent = 'Échec du téléversement';
          uploadStatus.textContent = data.error || 'Erreur inconnue';
          uploadStatus.className = 'form-status form-error';
          setTimeout(() => {
            uploadProgress.classList.add('hidden-section');
            uploadBtn.disabled = false;
          }, 4000);
        }
      } catch (err) {
        progressBar.classList.remove('progress-complete');
        progressBar.classList.add('progress-error');
        progressText.textContent = 'Erreur réseau';
        uploadStatus.textContent = 'Erreur de communication';
        uploadStatus.className = 'form-status form-error';
        setTimeout(() => {
          uploadProgress.classList.add('hidden-section');
          uploadBtn.disabled = false;
        }, 4000);
      }
    });
  }
});
