/**
 * A.N.A.N.A.S — Upload : image magnet links CRUD, bulk import
 */
UploadModule.imageMagnets = (function () {
  function createEntry(magnetValue, labelValue) {
    var container = document.getElementById('imageMagnetEntries');
    if (!container) return;

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
    labelInput.placeholder = "Nom de l'image (ex: Carte 2024)";
    labelInput.className = 'form-control flex-2';
    labelInput.value = labelValue || '';

    var removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-outline';
    removeBtn.textContent = '\u2715';
    removeBtn.addEventListener('click', function() { entry.remove(); });

    entry.appendChild(magnetInput);
    entry.appendChild(labelInput);
    entry.appendChild(removeBtn);
    container.appendChild(entry);
  }

  function collectLinks() {
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

  function init() {
    var addImageMagnetBtn = document.getElementById('addImageMagnetBtn');
    var bulkImageMagnetBtn = document.getElementById('bulkImageMagnetBtn');
    var bulkImageTextarea = document.getElementById('bulkImageTextarea');
    var bulkImageCount = document.getElementById('bulkImageCount');
    var bulkImageConfirm = document.getElementById('bulkImageConfirm');
    var bulkImageCancel = document.getElementById('bulkImageCancel');

    if (addImageMagnetBtn) {
      addImageMagnetBtn.addEventListener('click', function() {
        createEntry('', '');
      });
    }

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

    if (bulkImageTextarea) {
      bulkImageTextarea.addEventListener('input', function() {
        var lines = bulkImageTextarea.value.split('\n').filter(function(l) { return l.trim(); });
        bulkImageCount.textContent = lines.length + ' liens d\u00e9tect\u00e9s';
        document.getElementById('bulkImageConfirm').textContent = 'Ajouter ces ' + lines.length + ' liens';
      });
    }

    if (bulkImageConfirm) {
      bulkImageConfirm.addEventListener('click', function() {
        var lines = bulkImageTextarea.value.split('\n').filter(function(l) { return l.trim(); });
        lines.forEach(function(line) {
          createEntry(line.trim(), '');
        });
        bulkImageTextarea.value = '';
        bulkImageCount.textContent = '0 liens d\u00e9tect\u00e9s';
        bulkImageConfirm.textContent = 'Ajouter ces X liens';
        document.getElementById('bulkImageMagnetGroup').classList.add('hidden-section');
      });
    }

    if (bulkImageCancel) {
      bulkImageCancel.addEventListener('click', function() {
        bulkImageTextarea.value = '';
        bulkImageCount.textContent = '0 liens d\u00e9tect\u00e9s';
        bulkImageConfirm.textContent = 'Ajouter ces X liens';
        document.getElementById('bulkImageMagnetGroup').classList.add('hidden-section');
      });
    }
  }

  return { init: init, createEntry: createEntry, collectLinks: collectLinks };
})();