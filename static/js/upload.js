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
  const dataFormatLevel = document.getElementById('data_format_level');
  const packMagnetGroup = document.getElementById('packMagnetGroup');
  const individualMagnetGroup = document.getElementById('individualMagnetGroup');
  const magnetEntries = document.getElementById('magnetEntries');
  const addMagnetBtn = document.getElementById('addMagnetBtn');

  let magnetEntryCount = 0;

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
      uploadBtn.disabled = true;
      uploadStatus.textContent = 'Préparation...';
      uploadStatus.className = 'form-status';
      uploadProgress.classList.remove('hidden-section');

      const dataText = dataInput ? dataInput.value : '';
      const lines = dataText.split('\n').filter(line => line.trim()).slice(0, MAX_LINES);

      if (!lines.length) {
        uploadStatus.textContent = 'Veuillez coller vos données';
        uploadStatus.className = 'form-status form-error';
        uploadBtn.disabled = false;
        uploadProgress.classList.add('hidden-section');
        return;
      }

      const formData = new FormData();
      formData.append('data_text', lines.join('\n'));
      formData.append('title', document.getElementById('title').value);
      formData.append('type', document.getElementById('type').value);
      formData.append('format_type', document.getElementById('format_type').value);
      formData.append('description', document.getElementById('description').value);
      formData.append('data_format_level', dataFormatLevel.value);
      formData.append('organization_id', document.getElementById('organization_id').value);
      if (dataFormatLevel.value === 'pack') {
        const magnetLink = document.getElementById('magnet_link').value;
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
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfMeta ? csrfMeta.content : '';
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
            type: document.getElementById('type').value,
            format_type: document.getElementById('format_type').value,
            description: document.getElementById('description').value,
            data_format_level: dataFormatLevel.value,
            organization_id: document.getElementById('organization_id').value || '',
          };

          if (vizName.value && vizUrl.value) {
            itemPayload.viz_link_name = vizName.value;
            itemPayload.viz_link_url = vizUrl.value;
          }

          if (dataFormatLevel.value === 'pack') {
            itemPayload.magnet_link = document.getElementById('magnet_link').value;
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
