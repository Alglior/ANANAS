var ImodPreview = (function () {
  function getFormValues() {
    var title = (document.getElementById('title') || {}).value || '';
    var description = (document.getElementById('description') || {}).value || '';
    var formatType = (document.getElementById('format_type') || {}).value || '';
    var license = (document.getElementById('license_type') || {}).value || '';
    var org = (document.getElementById('organization_id') || {}).value || '';

    var tagsInput = document.getElementById('tags');
    var tags = tagsInput ? tagsInput.value.split(',').filter(function (t) { return t.trim(); }) : [];

    var dataFmtLevel = document.querySelector('input[name="data_format_level"]:checked');
    var fmtLevel = dataFmtLevel ? dataFmtLevel.value : 'simple';

    var magnetEntries = document.querySelectorAll('#magnetEntries .magnet-entry input[type="text"]');
    var magnetCount = 0;
    for (var i = 0; i < magnetEntries.length; i++) {
      if (magnetEntries[i].value.trim()) magnetCount++;
    }

    var imgMagnetEntries = document.querySelectorAll('#imageMagnetEntries .image-magnet-entry input[type="text"]');
    var imgMagnetCount = 0;
    for (var j = 0; j < imgMagnetEntries.length; j++) {
      if (imgMagnetEntries[j].value.trim()) imgMagnetCount++;
    }

    var vizName = (document.getElementById('viz_name') || {}).value || '';
    var vizUrl = (document.getElementById('viz_url') || {}).value || '';

    return {
      title: title,
      description: description,
      formatType: formatType,
      license: license,
      org: org,
      tags: tags,
      fmtLevel: fmtLevel,
      magnetCount: magnetCount,
      imgMagnetCount: imgMagnetCount,
      vizName: vizName,
      vizUrl: vizUrl
    };
  }

  function compute(values) {
    var meta = 0;
    if (values.description.length > 0) {
      meta += 1;
      if (values.description.length > 100) meta += 1;
    }
    if (values.tags.length >= 3) meta += 2;
    else if (values.tags.length >= 1) meta += 1;
    if (values.license) meta += 2;
    meta += 1;
    if (values.org) meta += 1;
    var metaPct = Math.min(meta, 8) / 8.0 * 45;

    var tech = 0;
    if (values.formatType) tech += 2;
    if (values.magnetCount > 0) tech += 2;
    var fmtLevels = { individual: 1, simple: 2, pack: 3 };
    tech += fmtLevels[values.fmtLevel] || 1;
    var techPct = Math.min(tech, 7) / 7.0 * 36;

    var rich = 0;
    if (values.imgMagnetCount >= 5) rich += 3;
    else if (values.imgMagnetCount >= 3) rich += 2;
    else if (values.imgMagnetCount >= 1) rich += 1;
    if (values.vizName && values.vizUrl) rich += 2;
    else if (values.vizName || values.vizUrl) rich += 1;
    var richPct = Math.min(rich, 5) / 5.0 * 19;

    var score = Math.round((metaPct + techPct + richPct) * 10) / 10;
    var level = 'Faible';
    if (score >= 70) level = 'Élevé';
    else if (score >= 40) level = 'Moyen';

    return {
      score: score,
      level: level,
      meta: Math.round(metaPct * 10) / 10,
      tech: Math.round(techPct * 10) / 10,
      rich: Math.round(richPct * 10) / 10,
      metaRaw: Math.min(meta, 8),
      techRaw: Math.min(tech, 7),
      richRaw: Math.min(rich, 5)
    };
  }

  function updatePreview() {
    var panel = document.getElementById('imodPreviewPanel');
    if (!panel) return;
    var values = getFormValues();
    var imod = compute(values);

    var scoreEl = panel.querySelector('.imod-preview-score');
    var levelEl = panel.querySelector('.imod-preview-level');
    var metaBar = panel.querySelector('.imod-preview-meta .imod-preview-fill');
    var techBar = panel.querySelector('.imod-preview-tech .imod-preview-fill');
    var richBar = panel.querySelector('.imod-preview-rich .imod-preview-fill');
    var metaVal = panel.querySelector('.imod-preview-meta .imod-preview-dim-value');
    var techVal = panel.querySelector('.imod-preview-tech .imod-preview-dim-value');
    var richVal = panel.querySelector('.imod-preview-rich .imod-preview-dim-value');

    if (scoreEl) {
      scoreEl.textContent = imod.score;
      scoreEl.className = 'imod-preview-score imod-preview-' + imod.level.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }
    if (levelEl) {
      levelEl.textContent = 'Niveau ' + imod.level;
      levelEl.className = 'imod-preview-level imod-preview-' + imod.level.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }
    if (metaBar) metaBar.style.width = (imod.metaRaw / 8 * 100) + '%';
    if (techBar) techBar.style.width = (imod.techRaw / 7 * 100) + '%';
    if (richBar) richBar.style.width = (imod.richRaw / 5 * 100) + '%';
    if (metaVal) metaVal.textContent = imod.meta;
    if (techVal) techVal.textContent = imod.tech;
    if (richVal) richVal.textContent = imod.rich;
  }

  function init() {
    var fields = ['title', 'description', 'format_type', 'license_type', 'organization_id',
      'viz_name', 'viz_url', 'tags'];
    for (var i = 0; i < fields.length; i++) {
      var el = document.getElementById(fields[i]);
      if (el) {
        el.addEventListener('input', updatePreview);
        el.addEventListener('change', updatePreview);
      }
    }

    var radios = document.querySelectorAll('input[name="data_format_level"]');
    for (var j = 0; j < radios.length; j++) {
      radios[j].addEventListener('change', updatePreview);
    }

    var tagChips = document.querySelectorAll('.tag-chip');
    for (var k = 0; k < tagChips.length; k++) {
      tagChips[k].addEventListener('click', function () {
        setTimeout(updatePreview, 50);
      });
    }

    var observer = new MutationObserver(function () {
      updatePreview();
    });
    var magnetSection = document.getElementById('magnetEntries');
    var imgMagnetSection = document.getElementById('imageMagnetEntries');
    if (magnetSection) observer.observe(magnetSection, { childList: true, subtree: true });
    if (imgMagnetSection) observer.observe(imgMagnetSection, { childList: true, subtree: true });

    var addMagnetBtns = document.querySelectorAll('#addMagnetBtn, #bulkMagnetConfirm, #addImageMagnetBtn, #bulkImageConfirm');
    for (var m = 0; m < addMagnetBtns.length; m++) {
      addMagnetBtns[m].addEventListener('click', function () {
        setTimeout(updatePreview, 100);
      });
    }

    updatePreview();
  }

  return { init: init, updatePreview: updatePreview };
})();

document.addEventListener('DOMContentLoaded', ImodPreview.init);