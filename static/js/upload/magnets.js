/**
 * A.N.A.N.A.S — Upload : magnet links CRUD, zoom pills, bulk import
 */
UploadModule.magnets = (function () {
  function createEntry(magnetValue, zoomValue) {
    var magnetEntries = document.getElementById('magnetEntries');
    if (!magnetEntries) return;

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
    removeBtn.textContent = '\u2715';
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
    var zoomLabels = ['IRIS', 'Communes', 'D\u00e9partements', 'R\u00e9gions', 'Pays'];

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

  function collectLinks() {
    var magnetEntries = document.getElementById('magnetEntries');
    if (!magnetEntries) return [];
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

  function init() {
    var magnetEntries = document.getElementById('magnetEntries');
    var addMagnetBtn = document.getElementById('addMagnetBtn');
    var bulkMagnetBtn = document.getElementById('bulkMagnetBtn');
    var bulkMagnetGroup = document.getElementById('bulkMagnetGroup');
    var bulkZoomPills = document.getElementById('bulkZoomPills');
    var bulkMagnetTextarea = document.getElementById('bulkMagnetTextarea');
    var bulkMagnetCount = document.getElementById('bulkMagnetCount');
    var bulkMagnetConfirm = document.getElementById('bulkMagnetConfirm');
    var bulkMagnetCancel = document.getElementById('bulkMagnetCancel');

    if (addMagnetBtn) {
      addMagnetBtn.addEventListener('click', function() {
        createEntry('', 'regions');
      });
    }

    if (magnetEntries) {
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
        bulkMagnetCount.textContent = lines.length + ' liens d\u00e9tect\u00e9s';
        bulkMagnetConfirm.textContent = 'Ajouter ces ' + lines.length + ' liens';
      });
    }

    if (bulkMagnetConfirm) {
      bulkMagnetConfirm.addEventListener('click', function() {
        var lines = bulkMagnetTextarea.value.split('\n').filter(function(l) { return l.trim(); });
        var activeZoom = bulkZoomPills.querySelector('.zoom-pill.active');
        var zoom = activeZoom ? activeZoom.getAttribute('data-zoom') : 'regions';
        lines.forEach(function(line) {
          createEntry(line.trim(), zoom);
        });
        bulkMagnetTextarea.value = '';
        bulkMagnetCount.textContent = '0 liens d\u00e9tect\u00e9s';
        bulkMagnetConfirm.textContent = 'Ajouter ces X liens';
        bulkMagnetGroup.classList.add('hidden-section');
      });
    }

    if (bulkMagnetCancel) {
      bulkMagnetCancel.addEventListener('click', function() {
        bulkMagnetTextarea.value = '';
        bulkMagnetCount.textContent = '0 liens d\u00e9tect\u00e9s';
        bulkMagnetConfirm.textContent = 'Ajouter ces X liens';
        bulkMagnetGroup.classList.add('hidden-section');
      });
    }

    createEntry('', 'regions');
  }

  return { init: init, createEntry: createEntry, collectLinks: collectLinks };
})();