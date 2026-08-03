var ImodPreview = (function () {
  var config = null;

  var defaultConfig = {
    weights: { meta: 45, tech: 36, rich: 19 },
    max_raw: { meta: 10, tech: 10, rich: 10 },
    thresholds: { high: 70, medium: 40 },
    levels: { high: "Élevé", medium: "Moyen", low: "Faible" },
    format_level_points: { individual: 1, simple: 2, pack: 3 }
  };

  function loadConfig(callback) {
    if (config) { if (callback) callback(); return; }
    fetch('/static/config/imod-config.json')
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (data) {
        config = data;
        if (callback) callback();
      })
      .catch(function () {
        config = defaultConfig;
        if (callback) callback();
      });
  }

  function validateMagnetLink(val) {
    return val && val.trim().indexOf('magnet:?xt=urn:btih:') === 0;
  }

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
    var validMagnetCount = 0;
    for (var i = 0; i < magnetEntries.length; i++) {
      var val = magnetEntries[i].value.trim();
      if (val) magnetCount++;
      if (validateMagnetLink(val)) validMagnetCount++;
    }

    var imgMagnetEntries = document.querySelectorAll('#imageMagnetEntries .image-magnet-entry input[type="text"]');
    var imgMagnetCount = 0;
    for (var j = 0; j < imgMagnetEntries.length; j++) {
      if (imgMagnetEntries[j].value.trim()) imgMagnetCount++;
    }

    var vizName = (document.getElementById('viz_name') || {}).value || '';
    var vizUrl = (document.getElementById('viz_url') || {}).value || '';

    var pdfMagnet = (document.getElementById('pdf_magnet_link') || {}).value || '';

    return {
      title: title,
      description: description,
      formatType: formatType,
      license: license,
      org: org,
      tags: tags,
      fmtLevel: fmtLevel,
      magnetCount: magnetCount,
      validMagnetCount: validMagnetCount,
      imgMagnetCount: imgMagnetCount,
      vizName: vizName,
      vizUrl: vizUrl,
      pdfMagnet: pdfMagnet
    };
  }

  function compute(values) {
    var cfg = config || defaultConfig;
    var w = cfg.weights;
    var mr = cfg.max_raw;
    var thr = cfg.thresholds;
    var lvls = cfg.levels;
    var fmtPts = cfg.format_level_points;

    var meta = 0;
    var metaItems = [];

    var descOk = values.description.length > 0;
    var descLong = values.description.length > 100;
    if (descOk) meta += 1;
    if (descLong) meta += 1;
    metaItems.push({ label: 'Description renseignée', ok: descOk, tip: 'Écrivez une description pour gagner +1', pts: descOk ? 1 : 0, max: 1 });
    metaItems.push({ label: 'Description détaillée (>100 car.)', ok: descLong, tip: 'Allongez la description à plus de 100 caractères pour gagner +1', pts: descLong ? 1 : 0, max: 1 });

    var tags3 = values.tags.length >= 3;
    var tags1 = values.tags.length >= 1;
    if (tags3) meta += 2;
    else if (tags1) meta += 1;
    metaItems.push({ label: '3 tags ou plus', ok: tags3, tip: 'Ajoutez au moins 3 tags pour gagner +2 (sinon +1 pour 1 tag)', pts: tags3 ? 2 : (tags1 ? 1 : 0), max: 2 });

    var hasLicense = !!values.license;
    if (hasLicense) meta += 2;
    metaItems.push({ label: 'Licence renseignée', ok: hasLicense, tip: 'Choisissez une licence pour gagner +2', pts: hasLicense ? 2 : 0, max: 2 });

    var hasAuthor = true;
    meta += 1;
    metaItems.push({ label: 'Auteur renseigné', ok: true, tip: 'Le champ auteur est automatiquement rempli', pts: 1, max: 1 });

    var hasOrg = !!values.org;
    if (hasOrg) meta += 1;
    metaItems.push({ label: 'Organisation rattachée', ok: hasOrg, tip: 'Rattachez une organisation pour gagner +1', pts: hasOrg ? 1 : 0, max: 1 });

    var hasPdf = validateMagnetLink(values.pdfMagnet);
    if (hasPdf) meta += 2;
    metaItems.push({ label: 'Documentation PDF (magnet)', ok: hasPdf, tip: 'Ajoutez un lien magnet vers un PDF de documentation pour gagner +2', pts: hasPdf ? 2 : 0, max: 2 });

    var metaClamped = Math.min(meta, mr.meta);
    var metaPct = metaClamped / mr.meta * w.meta;

    var tech = 0;
    var techItems = [];

    var hasFmt = !!values.formatType;
    if (hasFmt) tech += 2;
    techItems.push({ label: 'Type de format renseigné', ok: hasFmt, tip: 'Précisez le type de format pour gagner +2', pts: hasFmt ? 2 : 0, max: 2 });

    var hasMagnet = values.validMagnetCount > 0;
    if (hasMagnet) tech += 2;
    techItems.push({ label: 'Lien magnet valide', ok: hasMagnet, tip: 'Ajoutez un lien magnet valide (magnet:?xt=urn:btih:...) pour gagner +2', pts: hasMagnet ? 2 : 0, max: 2 });

    var fmtVal = fmtPts[values.fmtLevel] || 1;
    tech += fmtVal;
    var fmtLabels = { individual: 'Fichiers individuels', simple: 'Fichier simple', pack: 'Pack complet' };
    techItems.push({ label: 'Niveau : ' + (fmtLabels[values.fmtLevel] || values.fmtLevel), ok: true, tip: 'Passez en mode "Pack" pour maximiser le score (+3 au lieu de +2 pour Simple)', pts: fmtVal, max: 3 });

    techItems.push({ label: 'Vérification admin (après publication)', ok: false, tip: 'Faites vérifier vos données par un administrateur après publication pour gagner +1', pts: 0, max: 1 });

    var techClamped = Math.min(tech, mr.tech);
    var techPct = techClamped / mr.tech * w.tech;

    var rich = 0;
    var richItems = [];

    var img5 = values.imgMagnetCount >= 5;
    var img3 = values.imgMagnetCount >= 3;
    var img1 = values.imgMagnetCount >= 1;
    if (img5) rich += 3;
    else if (img3) rich += 2;
    else if (img1) rich += 1;
    richItems.push({ label: 'Images galerie (magnets)', ok: img5, tip: 'Ajoutez 5 magnets d\'image pour gagner +3 (3=+2, 1=+1)', pts: img5 ? 3 : (img3 ? 2 : (img1 ? 1 : 0)), max: 3 });

    var hasViz = !!(values.vizName && values.vizUrl);
    var hasVizPartial = !!(values.vizName || values.vizUrl);
    if (hasViz) rich += 2;
    else if (hasVizPartial) rich += 1;
    richItems.push({ label: 'Lien de visualisation', ok: hasViz, tip: 'Remplissez le nom ET l\'URL pour gagner +2 (un seul champ = +1)', pts: hasViz ? 2 : (hasVizPartial ? 1 : 0), max: 2 });

    var hasImgMagnets = values.imgMagnetCount > 0;
    if (hasImgMagnets) rich += 1;
    richItems.push({ label: 'Magnets image', ok: hasImgMagnets, tip: 'Ajoutez des magnets aux images de la galerie pour gagner +1', pts: hasImgMagnets ? 1 : 0, max: 1 });

    var richClamped = Math.min(rich, mr.rich);
    var richPct = richClamped / mr.rich * w.rich;

    var score = Math.round((metaPct + techPct + richPct) * 10) / 10;
    var level = lvls.low;
    if (score >= thr.high) level = lvls.high;
    else if (score >= thr.medium) level = lvls.medium;

    var maxPossible = w.meta + w.tech + w.rich;
    var gap = Math.round((maxPossible - score) * 10) / 10;

    return {
      score: score,
      level: level,
      meta: Math.round(metaPct * 10) / 10,
      tech: Math.round(techPct * 10) / 10,
      rich: Math.round(richPct * 10) / 10,
      metaRaw: metaClamped,
      techRaw: techClamped,
      richRaw: richClamped,
      metaItems: metaItems,
      techItems: techItems,
      richItems: richItems,
      maxPossible: maxPossible,
      gap: gap
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
    var cfg = config || defaultConfig;
    var w = cfg.weights;

    if (scoreEl) {
      scoreEl.textContent = imod.score;
      scoreEl.className = 'imod-preview-score imod-preview-' + imod.level.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }
    if (levelEl) {
      levelEl.textContent = 'Niveau ' + imod.level;
      levelEl.className = 'imod-preview-level imod-preview-' + imod.level.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }
    if (metaBar) metaBar.style.width = (imod.meta / w.meta * 100) + '%';
    if (techBar) techBar.style.width = (imod.tech / w.tech * 100) + '%';
    if (richBar) richBar.style.width = (imod.rich / w.rich * 100) + '%';
    if (metaVal) metaVal.textContent = imod.meta + '/' + w.meta;
    if (techVal) techVal.textContent = imod.tech + '/' + w.tech;
    if (richVal) richVal.textContent = imod.rich + '/' + w.rich;

    var checklist = panel.querySelector('.imod-checklist');
    if (!checklist) return;

    var allItems = [
      { label: 'Meta — Qualité documentaire', items: imod.metaItems, pts: imod.meta, max: w.meta, dim: 'meta' },
      { label: 'Tech — Précision technique', items: imod.techItems, pts: imod.tech, max: w.tech, dim: 'tech' },
      { label: 'Rich — Richesse du contenu', items: imod.richItems, pts: imod.rich, max: w.rich, dim: 'rich' }
    ];

    var html = '';
    for (var d = 0; d < allItems.length; d++) {
      var section = allItems[d];
      html += '<div class="imod-check-section">';
      html += '<div class="imod-check-header">';
      html += '<span class="imod-check-title">' + section.label + '</span>';
      html += '<span class="imod-check-score">' + section.pts + '/' + section.max + '</span>';
      html += '</div>';
      html += '<ul class="imod-check-list">';
      for (var c = 0; c < section.items.length; c++) {
        var item = section.items[c];
        var cls = item.ok ? 'imod-check-ok' : (item.pts > 0 ? 'imod-check-partial' : 'imod-check-miss');
        if (item.pts === item.max) cls = 'imod-check-ok';
        html += '<li class="' + cls + '">';
        html += '<span class="imod-check-icon">' + (item.pts === item.max ? '&#10003;' : (item.pts > 0 ? '&#9679;' : '&#10007;')) + '</span>';
        html += '<span class="imod-check-label">' + item.label + '</span>';
        html += '<span class="imod-check-pts">+' + item.pts + '</span>';
        if (!item.ok) {
          html += '<span class="imod-check-tip" title="' + item.tip + '">&#9432;</span>';
        }
        html += '</li>';
      }
      html += '</ul>';
      html += '</div>';
    }

    var maxPts = imod.maxPossible;
    html += '<div class="imod-check-footer">';
    html += '<span class="imod-check-gap">Potentiel max : ' + maxPts + '/100 &mdash; il vous manque ' + imod.gap + ' pts';
    if (imod.gap > 0) {
      html += '<br><span class="imod-check-advice">Conseil : remplissez les critères marqués &#10007; pour maximiser votre score avant publication.</span>';
    } else {
      html += '<br><span class="imod-check-advice">Félicitations, tous les critères disponibles sont remplis !</span>';
    }
    html += '</span></div>';

    checklist.innerHTML = html;
  }

  function init() {
    loadConfig(function () {
      var fields = ['title', 'description', 'format_type', 'license_type', 'organization_id',
        'viz_name', 'viz_url', 'tags', 'pdf_magnet_link'];
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
      if (magnetSection) {
        observer.observe(magnetSection, { childList: true, subtree: true });
        magnetSection.addEventListener('input', updatePreview);
      }
      if (imgMagnetSection) {
        observer.observe(imgMagnetSection, { childList: true, subtree: true });
        imgMagnetSection.addEventListener('input', updatePreview);
      }

      var addMagnetBtns = document.querySelectorAll('#addMagnetBtn, #bulkMagnetConfirm, #addImageMagnetBtn, #bulkImageConfirm');
      for (var m = 0; m < addMagnetBtns.length; m++) {
        addMagnetBtns[m].addEventListener('click', function () {
          setTimeout(updatePreview, 100);
        });
      }

      updatePreview();
    });
  }

  return { init: init, updatePreview: updatePreview };
})();

document.addEventListener('DOMContentLoaded', ImodPreview.init);