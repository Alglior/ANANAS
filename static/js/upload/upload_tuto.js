(function() {
  const TUTO_KEY = 'upload_tuto_done_v7';

  function currentTab() {
    var active = document.querySelector('.upload-tab.active');
    return active ? active.getAttribute('data-tab') : 'publish';
  }

  function switchToTab(tabName) {
    var tabs = document.querySelectorAll('.upload-tab');
    var tabContents = document.querySelectorAll('.upload-tab-content');
    var targetTab = document.querySelector('.upload-tab[data-tab="' + tabName + '"]');
    if (!targetTab) return;

    tabs.forEach(function(t) { t.classList.remove('active'); });
    tabContents.forEach(function(c) { c.classList.remove('active'); });
    targetTab.classList.add('active');
    var content = document.getElementById('tab-' + tabName);
    if (content) content.classList.add('active');
  }

  const steps = [
    {
      tab: 'publish',
      target: '.publications-tuto-section',
      position: 'bottom',
      text: '<strong>Tutoriel vidéo</strong> — Besoin d\'aide ? Cliquez sur <strong>▶ Voir le tutoriel</strong> pour apprendre à télécharger ou créer un lien Magnet. Ce bouton est disponible dans chaque onglet.',
    },
    {
      tab: 'publish',
      target: '#jsonDropZone',
      position: 'bottom',
      text: '<strong>Import JSON</strong> — Déposez ici un ou plusieurs fichiers JSON pour pré-remplir automatiquement les métadonnées de la fiche (utile pour réimporter une fiche existante).',
    },
    {
      tab: 'publish',
      target: '#title',
      position: 'bottom',
      text: '<strong>Titre</strong> — Donnez un nom à votre publication. C\'est le titre qui apparaîtra dans le catalogue.',
    },
    {
      tab: 'publish',
      target: '#type, #format_type',
      position: 'bottom',
      text: '<strong>Type et format</strong> — Choisissez la catégorie de contenu (géodonnées, carte, application) et le format technique du fichier.',
    },
    {
      tab: 'publish',
      target: '#description',
      position: 'bottom',
      text: '<strong>Description</strong> — Décrivez le contenu, la méthode de collecte et les conditions d\'utilisation. Cette description sera visible publiquement.',
    },
    {
      tab: 'publish',
      target: '#tagSelector',
      position: 'top',
      text: '<strong>Tags</strong> — Sélectionnez des tags par catégorie ou saisissez vos propres mots-clés pour rendre vos données plus faciles à retrouver dans le catalogue.',
    },
    {
      tab: 'publish',
      target: '#organization_id',
      position: 'bottom',
      text: '<strong>Organisation</strong> — Associez votre publication à une organisation (optionnel). Laissez vide pour une publication personnelle.',
    },
    {
      tab: 'publish',
      target: '#license_type',
      position: 'bottom',
      text: '<strong>Licence</strong> — Choisissez les conditions d\'utilisation de vos données (CC-BY, Licence Ouverte, Domaine Public, etc.).',
    },
    {
      tab: 'publish',
      target: '#dataFormatLevelGroup',
      position: 'top',
      text: '<strong>Format des données</strong> — Choisissez <strong>Simple</strong> (un seul fichier, une seule couche), <strong>Pack</strong> (un seul fichier multi-couches) ou <strong>Individuelles</strong> (plusieurs fichiers distincts).',
    },
    {
      tab: 'publish',
      target: '#dataTextInputGroup',
      position: 'top',
      text: '<strong>Données</strong> — Collez un aperçu de votre tableau en CSV (optionnel). Seules les 50 premières lignes seront affichées dans le catalogue.',
    },
    {
      tab: 'publish',
      target: '#magnetSection',
      position: 'top',
      text: '<strong>Liens Magnet</strong> — Ajoutez vos liens Magnet torrent. <strong>+ Ajouter un lien</strong> pour un seul lien, <strong>Ajouter en lot</strong> pour en coller plusieurs d\'un coup. Sélectionnez le niveau de zoom pour chaque lien.',
    },
    {
      tab: 'publish',
      target: '#imageMagnetEntries',
      position: 'top',
      text: '<strong>Images</strong> — Optionnel. Ajoutez des liens Magnet pointant vers des images (PNG, JPG...). Elles seront téléchargées automatiquement par le serveur.',
    },
    {
      tab: 'publish',
      target: '#pdf_magnet_link',
      position: 'top',
      text: '<strong>Documentation PDF</strong> — Optionnel. Ajoutez un lien Magnet vers un document PDF (notice, rapport technique). Cela ajoute des points à votre score IMOD.',
    },
    {
      tab: 'publish',
      target: '#viz_name, #viz_url',
      position: 'top',
      text: '<strong>Visualisation</strong> — Optionnel. Ajoutez un lien vers un service de visualisation externe (WMS, WFS, Mapbox, etc.).',
    },
    {
      tab: 'publish',
      target: '#imodPreviewPanel',
      position: 'top',
      text: '<strong>Score IMOD</strong> — Aperçu en temps réel de l\'indice de qualité de vos métadonnées (Meta, Tech, Rich). Remplissez les champs pour améliorer votre score avant publication.',
    },
    {
      tab: 'publish',
      target: '.upload-actions',
      position: 'top',
      switchTab: 'drafts',
      text: '<strong>Publier ou brouillon</strong> — <strong>Publier</strong> rend votre contenu visible. <strong>Brouillon</strong> le sauvegarde pour le finir plus tard. <strong>Télécharger la fiche</strong> exporte les métadonnées en JSON. Cliquez sur <strong>Brouillons</strong> pour continuer.',
    },
    {
      tab: 'drafts',
      target: '#tab-drafts .upload-history-list, #tab-drafts .no-data-message',
      position: 'top',
      switchTab: 'publications',
      text: '<strong>Mes brouillons</strong> — Retrouvez tous vos brouillons en cours ici. Modifiez-les ou mettez-les à la corbeille. Cliquez sur <strong>Mes publications</strong> pour voir vos contenus déjà publiés.',
    },
    {
      tab: 'publications',
      target: '#tab-publications .upload-history-list, #tab-publications .no-data-message',
      position: 'top',
      switchTab: 'trash',
      text: '<strong>Mes publications</strong> — Consultez les données que vous avez déjà publiées sur le catalogue. Cliquez sur <strong>Corbeille</strong> pour voir les éléments supprimés.',
    },
    {
      tab: 'trash',
      target: '#tab-trash .trash-hint, #tab-trash .upload-history-list, #tab-trash .no-data-message',
      position: 'top',
      text: '<strong>Corbeille</strong> — Les brouillons supprimés restent 7 jours. Vous pouvez les <strong>restaurer</strong> ou les <strong>supprimer définitivement</strong>.',
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

  function clearHighlights() {
    document.querySelectorAll('.tuto-highlight').forEach(function(el) {
      el.classList.remove('tuto-highlight');
    });
  }

  function showStep(index) {
    if (index < 0) index = 0;
    if (index >= steps.length) { endTutorial(); return; }
    currentStep = index;

    clearHighlights();

    var step = steps[index];

    if (step.tab && step.tab !== currentTab()) {
      switchToTab(step.tab);
    }

    var target = document.querySelector(step.target);
    if (!target) {
      setTimeout(function() { showStep(currentStep); }, 200);
      return;
    }

    target.classList.add('tuto-highlight');
    stepCur.textContent = index + 1;
    stepText.innerHTML = step.text;

    overlay.classList.remove('hidden-section');
    tooltip.classList.remove('hidden-section');

    target.scrollIntoView({ behavior: 'smooth', block: 'center' });

    btnPrev.style.visibility = index === 0 ? 'hidden' : 'visible';

    if (step.switchTab) {
      var tabLabels = { drafts: 'Mes brouillons', publications: 'Mes publications', trash: 'Corbeille' };
      btnNext.textContent = (tabLabels[step.switchTab] || 'Continuer') + ' →';
    } else if (index === steps.length - 1) {
      btnNext.textContent = 'Terminer ✓';
    } else {
      btnNext.textContent = 'Suivant →';
    }

    tooltip.style.top = '-9999px';
    tooltip.style.left = '-9999px';
    requestAnimationFrame(function() { positionTooltip(target); });
  }

  function nextStep() {
    var step = steps[currentStep];
    if (step.switchTab) {
      switchToTab(step.switchTab);
    }
    showStep(currentStep + 1);
  }

  function prevStep() {
    var prevIdx = currentStep - 1;
    if (prevIdx < 0) return;

    var prevStepObj = steps[prevIdx];
    if (prevStepObj.tab && prevStepObj.tab !== currentTab()) {
      switchToTab(prevStepObj.tab);
    }

    showStep(prevIdx);
  }

  function endTutorial() {
    overlay.classList.add('hidden-section');
    tooltip.classList.add('hidden-section');
    clearHighlights();
    if (dontShow.checked) {
      localStorage.setItem(TUTO_KEY, '1');
    }
  }

  if (btnNext) btnNext.addEventListener('click', nextStep);
  if (btnPrev) btnPrev.addEventListener('click', prevStep);
  if (btnSkip) btnSkip.addEventListener('click', endTutorial);

  var relaunch = document.getElementById('relaunchTuto');
  if (relaunch) {
    relaunch.addEventListener('click', function(e) {
      e.preventDefault();
      switchToTab('publish');
      showStep(0);
    });
  }

  if (!localStorage.getItem(TUTO_KEY)) {
    setTimeout(function() { showStep(0); }, 600);
  }
})();