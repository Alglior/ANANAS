/**
 * A.N.A.N.A.S — Upload : magnet links CRUD, zoom pills, bulk import
 */
UploadModule.magnets = (function () {
  var singleEntryMode = false;
  var multiZoomMode = false;

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
    removeBtn.className = 'btn btn-outline magnet-remove-btn';
    removeBtn.textContent = '\u2715';
    removeBtn.addEventListener('click', function() {
      var allEntries = magnetEntries.querySelectorAll('.magnet-entry');
      if (singleEntryMode || allEntries.length <= 1) return;
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

    var zoomLevels = ['iris', 'communes', 'cantons', 'departements', 'regions', 'pays'];
    var zoomLabels = ['IRIS', 'Communes', 'Cantons', 'D\u00e9partements', 'R\u00e9gions', 'Pays'];

    zoomLevels.forEach(function(z, i) {
      var pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'zoom-pill';
      pill.setAttribute('data-zoom', z);
      pill.textContent = zoomLabels[i];
      var zoomVals = (zoomValue || 'regions').split(',');
      if (zoomVals.indexOf(z) !== -1) {
        pill.classList.add('active');
      }
      pills.appendChild(pill);
    });

    entry.appendChild(row);
    entry.appendChild(pills);
    entry.appendChild(zoomInput);
    magnetEntries.appendChild(entry);
  }

  function setSingleEntryMode(enabled, multiZoom) {
    singleEntryMode = enabled;
    multiZoomMode = enabled && multiZoom;
    var magnetEntries = document.getElementById('magnetEntries');
    var addBtn = document.getElementById('addMagnetBtn');
    var bulkBtn = document.getElementById('bulkMagnetBtn');
    var bulkGroup = document.getElementById('bulkMagnetGroup');

    if (addBtn) addBtn.style.display = enabled ? 'none' : '';
    if (bulkBtn) bulkBtn.style.display = enabled ? 'none' : '';
    if (bulkGroup) bulkGroup.classList.add('hidden-section');

    if (!magnetEntries) return;
    var entries = magnetEntries.querySelectorAll('.magnet-entry');

    if (enabled) {
      while (entries.length > 1) {
        entries[entries.length - 1].remove();
        entries = magnetEntries.querySelectorAll('.magnet-entry');
      }
      entries.forEach(function(entry) {
        var removeBtn = entry.querySelector('.magnet-remove-btn');
        if (removeBtn) removeBtn.style.display = 'none';
        if (multiZoom) {
          var pills = entry.querySelectorAll('.zoom-pill');
          pills.forEach(function(p) {
            p.classList.toggle('multi-select', true);
          });
        }
      });
    } else {
      entries.forEach(function(entry) {
        var removeBtn = entry.querySelector('.magnet-remove-btn');
        if (removeBtn) removeBtn.style.display = '';
        var multiPills = entry.querySelectorAll('.zoom-pill.multi-select');
        multiPills.forEach(function(p) {
          p.classList.remove('multi-select', 'active');
        });
        var allPills = entry.querySelectorAll('.zoom-pill');
        allPills.forEach(function(p) { p.classList.remove('active'); });
        var firstPill = entry.querySelector('.zoom-pill');
        if (firstPill) firstPill.classList.add('active');
        var hidden = entry.querySelector('input[name="zoom_level[]"]');
        if (hidden && firstPill) hidden.value = firstPill.getAttribute('data-zoom');
      });
    }
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
        if (multiZoomMode) {
          var activePills = entry.querySelectorAll('.zoom-pill.active');
          var zoomLevels = [];
          activePills.forEach(function(p) { zoomLevels.push(p.getAttribute('data-zoom')); });
          links.push({
            magnet_link: val,
            zoom_levels: zoomLevels,
            zoom_level: zoomLevels.join(',')
          });
        } else {
          links.push({
            magnet_link: val,
            zoom_level: hidden ? hidden.value : 'regions'
          });
        }
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

        if (pill.classList.contains('multi-select')) {
          pill.classList.toggle('active');
          var activePills = entry.querySelectorAll('.zoom-pill.active');
          var zoomVals = [];
          activePills.forEach(function(p) { zoomVals.push(p.getAttribute('data-zoom')); });
          var hidden = entry.querySelector('input[name="zoom_level[]"]');
          if (hidden) {
            hidden.value = zoomVals.join(',');
          }
        } else {
          entry.querySelectorAll('.zoom-pill').forEach(function(p) { p.classList.remove('active'); });
          pill.classList.add('active');
          var hidden = entry.querySelector('input[name="zoom_level[]"]');
          if (hidden) {
            hidden.value = pill.getAttribute('data-zoom');
          }
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
        if (singleEntryMode) return;
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

    var packRadio = document.querySelector('input[name="data_format_level"][value="pack"]');
    if (packRadio) {
      packRadio.addEventListener('change', function() {
        if (this.checked) setSingleEntryMode(true, true);
      });
    }
    var simpleRadio = document.querySelector('input[name="data_format_level"][value="simple"]');
    if (simpleRadio) {
      simpleRadio.addEventListener('change', function() {
        if (this.checked) setSingleEntryMode(true, false);
      });
    }
    var indivRadio = document.querySelector('input[name="data_format_level"][value="individual"]');
    if (indivRadio) {
      indivRadio.addEventListener('change', function() {
        if (this.checked) setSingleEntryMode(false, false);
      });
    }

    if (document.querySelector('input[name="data_format_level"]:checked')) {
      var checked = document.querySelector('input[name="data_format_level"]:checked').value;
      if (checked === 'pack') setSingleEntryMode(true, true);
      else if (checked === 'simple') setSingleEntryMode(true, false);
    }

    createEntry('', 'regions');
  }

  return { init: init, createEntry: createEntry, collectLinks: collectLinks, setSingleEntryMode: setSingleEntryMode };
})();