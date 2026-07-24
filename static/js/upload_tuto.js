(function() {
  const TUTO_KEY = 'upload_tuto_done_v2';

  const steps = [
    {
      target: '#title',
      position: 'bottom',
      text: '<strong>Titre</strong> — Donnez un nom à votre publication. C\'est le titre qui apparaîtra dans le catalogue.',
    },
    {
      target: '#type',
      position: 'bottom',
      text: '<strong>Type et format</strong> — Choisissez la catégorie de contenu (géodonnées, carte, application) et le format technique.',
    },
    {
      target: '#magnetSection',
      position: 'top',
      text: '<strong>Données</strong> — Collez un aperçu CSV (optionnel) et ajoutez vos liens Magnet. Le bouton <strong>+</strong> ajoute un lien, <strong>Ajouter en lot</strong> permet d\'en coller plusieurs d\'un coup.',
    },
    {
      target: '.zoom-pills',
      position: 'top',
      text: '<strong>Niveau de zoom</strong> — Pour chaque lien Magnet, cliquez sur le niveau géographique : IRIS, Communes, Départements, Régions ou Pays.',
    },
    {
      target: '#imageMagnetEntries',
      position: 'top',
      text: '<strong>Images</strong> — Optionnel. Ajoutez des liens Magnet pointant vers des images (PNG, JPG...). Elles seront téléchargées automatiquement par le serveur.',
    },
    {
      target: '.upload-actions',
      position: 'top',
      text: '<strong>Publier ou brouillon</strong> — <strong>Publier</strong> rend votre contenu visible. <strong>Brouillon</strong> le sauvegarde pour le finir plus tard.',
    },
    {
      target: '.upload-tab[data-tab="drafts"]',
      position: 'bottom',
      text: '<strong>Mes brouillons</strong> — Retrouvez tous vos brouillons en cours ici. Modifiez-les ou mettez-les à la corbeille.',
    },
    {
      target: '.upload-tab[data-tab="trash"]',
      position: 'bottom',
      text: '<strong>Corbeille</strong> — Les brouillons supprimés restent 7 jours. Vous pouvez les restaurer ou les supprimer définitivement.',
    },
  ];

  let currentStep = 0;

  var overlay = document.getElementById('tutoOverlay');
  var tooltip = document.getElementById('tutoTooltip');
  var stepCur = document.getElementById('tutoStepCurrent');
  var stepTotal = document.getElementById('tutoStepTotal');
  var stepText = document.getElementById('tutoStepText');
  var btnPrev = document.getElementById('tutoPrev');
  var btnNext = document.getElementById('tutoNext');
  var btnSkip = document.getElementById('tutoSkip');
  var dontShow = document.getElementById('tutoDontShow');

  if (overlay) document.body.appendChild(overlay);
  if (tooltip) document.body.appendChild(tooltip);

  if (stepTotal) stepTotal.textContent = steps.length;

  function positionTooltip(targetEl) {
    var rect = targetEl.getBoundingClientRect();
    var step = steps[currentStep];
    var ttipW = 340;
    var ttipH = tooltip.offsetHeight || 200;

    var preferred = step.position;

    if (preferred === 'bottom' && rect.bottom + 12 + ttipH > window.innerHeight - 10) {
      preferred = 'top';
    } else if (preferred === 'top' && rect.top - 12 - ttipH < 10) {
      preferred = 'bottom';
    }

    var top, left;
    if (preferred === 'bottom') {
      top = rect.bottom + 12;
      left = rect.left + rect.width / 2 - ttipW / 2;
    } else if (preferred === 'top') {
      top = rect.top - ttipH - 12;
      left = rect.left + rect.width / 2 - ttipW / 2;
    } else if (preferred === 'right') {
      top = rect.top + rect.height / 2 - ttipH / 2;
      left = rect.right + 12;
    } else {
      top = rect.top + rect.height / 2 - ttipH / 2;
      left = rect.left - ttipW - 12;
    }

    top = Math.max(10, Math.min(top, window.innerHeight - ttipH - 10));
    left = Math.max(10, Math.min(left, window.innerWidth - ttipW - 10));

    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
    tooltip.className = 'tuto-tooltip pos-' + preferred;
  }

  function showStep(index) {
    if (index < 0) index = 0;
    if (index >= steps.length) { endTutorial(); return; }
    currentStep = index;

    document.querySelectorAll('.tuto-highlight').forEach(function(el) { el.classList.remove('tuto-highlight'); });

    var step = steps[index];
    var target = document.querySelector(step.target);
    if (!target) { showStep(index + 1); return; }

    target.classList.add('tuto-highlight');
    stepCur.textContent = index + 1;
    stepText.innerHTML = step.text;

    overlay.classList.remove('hidden-section');
    tooltip.classList.remove('hidden-section');

    target.scrollIntoView({ behavior: 'smooth', block: 'center' });

    btnPrev.style.visibility = index === 0 ? 'hidden' : 'visible';
    btnNext.textContent = index === steps.length - 1 ? 'Terminer ✓' : 'Suivant →';

    tooltip.style.top = '-9999px';
    tooltip.style.left = '-9999px';
    requestAnimationFrame(function() { positionTooltip(target); });
  }

  function endTutorial() {
    overlay.classList.add('hidden-section');
    tooltip.classList.add('hidden-section');
    document.querySelectorAll('.tuto-highlight').forEach(function(el) { el.classList.remove('tuto-highlight'); });
    if (dontShow.checked) {
      localStorage.setItem(TUTO_KEY, '1');
    }
  }

  if (btnNext) btnNext.addEventListener('click', function() { showStep(currentStep + 1); });
  if (btnPrev) btnPrev.addEventListener('click', function() { showStep(currentStep - 1); });
  if (btnSkip) btnSkip.addEventListener('click', endTutorial);

  var relaunch = document.getElementById('relaunchTuto');
  if (relaunch) {
    relaunch.addEventListener('click', function(e) {
      e.preventDefault();
      showStep(0);
    });
  }

  if (!localStorage.getItem(TUTO_KEY)) {
    setTimeout(function() { showStep(0); }, 600);
  }
})();
