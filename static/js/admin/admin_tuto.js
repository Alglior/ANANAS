(function() {
  const TUTO_KEY = 'admin_panel_tuto_v7';
  const STEP_KEY = 'admin_panel_tuto_step_v7';
  const ACTIVE_KEY = 'admin_panel_tuto_active_v7';

  function currentPage() {
    var p = window.location.pathname;
    if (p.startsWith('/admin/moderation')) return 'moderation';
    if (p.startsWith('/admin/settings')) return 'settings';
    if (p.startsWith('/admin/audit')) return 'audit';
    return 'users';
  }

  function activateStepTabs(step) {
    if (step.settingsTab) {
      var sb = document.querySelector('.settings-sidebar-tab[data-settings-tab="' + step.settingsTab + '"]');
      if (sb) sb.click();
    }
    if (step.innerTab) {
      var it = document.querySelector('.settings-inner-tab[data-inner-tab="' + step.innerTab + '"]');
      if (it) it.click();
    }
    if (step.modTab) {
      var mt = document.querySelector('.mod-tab[data-tab="' + step.modTab + '"]');
      if (mt) mt.click();
    }
  }

  var steps = [
    {
      page: 'any',
      target: '.admin-nav',
      position: 'bottom',
      text: '<strong>Navigation d\'administration</strong> — Cette barre donne accès aux 4 sections du panneau : <strong>Utilisateurs</strong>, <strong>Modération</strong>, <strong>Paramètres</strong> et <strong>Journal d\'audits</strong>. Cliquez sur <strong>Suivant</strong> pour découvrir chaque section.',
    },
    {
      page: 'any',
      target: '.admin-nav a:nth-child(1)',
      position: 'bottom',
      navigateTo: '/admin/users',
      text: '<strong>Utilisateurs</strong> — Gérez les comptes : consultez la liste, <strong>bannissez</strong> ou <strong>débannissez</strong> les utilisateurs.',
    },
    {
      page: 'users',
      target: '.admin-page table',
      position: 'top',
      text: '<strong>Liste des utilisateurs</strong> — Chaque ligne affiche l\'ID, le nom, le pseudo et le statut. Les boutons <strong>Bannir/Débannir</strong> permettent de contrôler l\'accès au site.',
    },
    {
      page: 'users',
      target: '.admin-nav a:nth-child(2)',
      position: 'bottom',
      navigateTo: '/admin/moderation',
      text: '<strong>Modération</strong> — Modérez les commentaires, les publications du catalogue, les signalements et les messages de contact.',
    },
    {
      page: 'moderation',
      target: '.mod-tabs',
      position: 'top',
      text: '<strong>Modération</strong> — Quatre onglets : <strong>Commentaires</strong>, <strong>Cartes, Applications &amp; Données</strong>, <strong>Signalements</strong> et <strong>Messages</strong>. Supprimez, vérifiez ou retirez la vérification du contenu.',
    },
    {
      page: 'moderation',
      target: '.mod-tab[data-tab="reports"], #report-status-filters, #reports-table',
      position: 'top',
      modTab: 'reports',
      text: '<strong>Signalements</strong> — Filtrez par statut (<strong>En attente</strong>, <strong>Résolu</strong>, <strong>Non fondé</strong>). Chaque signalement peut être marqué comme résolu ou rejeté.',
    },
    {
      page: 'moderation',
      target: '#contact-msg-filters, #contact-msgs-table',
      position: 'top',
      modTab: 'messages',
      text: '<strong>Messages de contact</strong> — Filtrez par statut (<strong>Tous</strong>, <strong>Non lus</strong>, <strong>Lus</strong>). Cliquez sur <strong>Voir</strong> pour lire le message complet, ou <strong>Supprimer</strong> pour l\'effacer.',
    },
    {
      page: 'moderation',
      target: '.admin-nav a:nth-child(3)',
      position: 'bottom',
      navigateTo: '/admin/settings',
      text: '<strong>Paramètres</strong> — Configurez le site : paramètres généraux, catalogues, page d\'accueil, étiquettes, réplication et sauvegarde.',
    },
    {
      page: 'settings',
      target: '.settings-sidebar-nav',
      position: 'right',
      text: '<strong>Paramètres</strong> — Six sections dans le menu latéral : <strong>Général</strong>, <strong>Catalogues</strong>, <strong>Accueil</strong>, <strong>Étiquettes</strong>, <strong>Réplication</strong> et <strong>Sauvegarde</strong>.',
    },
    {
      page: 'settings',
      target: '#settings-tab-catalogues .settings-card',
      position: 'top',
      settingsTab: 'catalogues',
      text: '<strong>Catalogues</strong> — Activez ou désactivez chaque catalogue de la plateforme. Un catalogue désactivé n\'est plus accessible et n\'apparaît plus dans la navigation.',
    },
    {
      page: 'settings',
      target: '.settings-inner-nav',
      position: 'top',
      settingsTab: 'accueil',
      text: '<strong>Accueil</strong> — Gérez les sections de la page d\'accueil : <strong>Sites miroirs</strong>, <strong>Données en avant</strong>, <strong>Packs GeoPackage</strong> et <strong>Fichiers simples</strong>.',
    },
    {
      page: 'settings',
      target: '#featured-table, #add-featured-btn',
      position: 'top',
      settingsTab: 'accueil',
      innerTab: 'featured',
      text: '<strong>Données en avant</strong> — Recherchez un item du catalogue et ajoutez-le à la section « Exemples de Données Disponibles ». Activez ou retirez les données facilement.',
    },
    {
      page: 'settings',
      target: '#tags-table',
      position: 'top',
      settingsTab: 'etiquettes',
      text: '<strong>Étiquettes</strong> — Gérez les <strong>catégories d\'étiquettes</strong> et leurs étiquettes associées pour le filtrage dans les formulaires.',
    },
    {
      page: 'settings',
      target: '#remote-url, .settings-card',
      position: 'top',
      settingsTab: 'replication',
      text: '<strong>Réplication</strong> — Répliquez les items d\'un catalogue depuis une autre instance A.N.A.N.A.S en fournissant son URL. Les items sont importés avec leurs fiches, tags et galeries.',
    },
    {
      page: 'settings',
      target: '#backup-download-btn, .settings-card',
      position: 'top',
      settingsTab: 'backup',
      text: '<strong>Sauvegarde</strong> — Téléchargez un dump complet de la base de données ou <strong>restaurez</strong> une sauvegarde existante.',
    },
    {
      page: 'settings',
      target: '.admin-nav a:nth-child(4)',
      position: 'bottom',
      navigateTo: '/admin/audit',
      text: '<strong>Journal d\'audits</strong> — Consultez l\'historique complet de toutes les actions administratives.',
    },
    {
      page: 'audit',
      target: '#audit-table, .mod-panel',
      position: 'top',
      text: '<strong>Journal d\'audits</strong> — Chaque entrée indique la <strong>date</strong>, l\'<strong>admin</strong>, l\'<strong>action</strong> effectuée et la <strong>cible</strong>. Idéal pour tracer toutes les opérations.',
    },
  ];

  var currentStep = 0;
  var isTransitioning = false;

  var overlay = document.getElementById('adminTutoOverlay');
  var tooltip = document.getElementById('adminTutoTooltip');
  var stepCur = document.getElementById('adminTutoStepCurrent');
  var stepTotal = document.getElementById('adminTutoStepTotal');
  var stepText = document.getElementById('adminTutoStepText');
  var btnPrev = document.getElementById('adminTutoPrev');
  var btnNext = document.getElementById('adminTutoNext');
  var btnSkip = document.getElementById('adminTutoSkip');
  var dontShow = document.getElementById('adminTutoDontShow');

  if (overlay) document.body.appendChild(overlay);
  if (tooltip) document.body.appendChild(tooltip);

  if (stepTotal) stepTotal.textContent = steps.length;

  function positionTooltip(targetEl) {
    var rect = targetEl.getBoundingClientRect();
    var step = steps[currentStep];
    var ttipW = 360;
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
    tooltip.className = 'admin-tuto-tooltip pos-' + preferred;
  }

  function clearHighlights() {
    document.querySelectorAll('.admin-tuto-highlight').forEach(function(el) {
      el.classList.remove('admin-tuto-highlight');
    });
  }

  function showStep(index) {
    if (index < 0) index = 0;
    if (index >= steps.length) { endTutorial(); return; }
    currentStep = index;

    clearHighlights();

    var step = steps[index];

    if (step.page !== 'any' && step.page !== currentPage()) {
      localStorage.setItem(ACTIVE_KEY, '1');
      localStorage.setItem(STEP_KEY, String(index));
      window.location.href = step.navigateTo || '/admin/' + step.page;
      return;
    }

    activateStepTabs(step);

    var target = document.querySelector(step.target);
    if (!target) {
      setTimeout(function() { showStep(currentStep); }, 300);
      return;
    }

    target.classList.add('admin-tuto-highlight');
    stepCur.textContent = index + 1;
    stepText.innerHTML = step.text;

    overlay.classList.remove('hidden-section');
    tooltip.classList.remove('hidden-section');

    target.scrollIntoView({ behavior: 'smooth', block: 'center' });

    btnPrev.style.visibility = index === 0 ? 'hidden' : 'visible';

    if (step.navigateTo) {
      btnNext.textContent = 'Ouvrir →';
    } else if (index === steps.length - 1) {
      btnNext.textContent = 'Terminer ✓';
    } else {
      btnNext.textContent = 'Suivant →';
    }

    tooltip.style.top = '-9999px';
    tooltip.style.left = '-9999px';
    requestAnimationFrame(function() { positionTooltip(target); });

    localStorage.setItem(STEP_KEY, String(index));
    localStorage.setItem(ACTIVE_KEY, '1');
  }

  function nextStep() {
    if (isTransitioning) return;
    var step = steps[currentStep];
    if (step.navigateTo) {
      isTransitioning = true;
      var nextIdx = currentStep + 1;
      localStorage.setItem(ACTIVE_KEY, '1');
      localStorage.setItem(STEP_KEY, String(nextIdx));
      window.location.href = step.navigateTo;
      return;
    }
    showStep(currentStep + 1);
  }

  function prevStep() {
    if (isTransitioning) return;
    var prevIdx = currentStep - 1;

    if (prevIdx < 0) return;

    var prevStepObj = steps[prevIdx];
    if (prevStepObj.page !== 'any' && prevStepObj.page !== currentPage()) {
      isTransitioning = true;
      localStorage.setItem(ACTIVE_KEY, '1');
      localStorage.setItem(STEP_KEY, String(prevIdx));
      window.location.href = prevStepObj.navigateTo || '/admin/' + prevStepObj.page;
      return;
    }

    showStep(prevIdx);
  }

  function endTutorial() {
    overlay.classList.add('hidden-section');
    tooltip.classList.add('hidden-section');
    clearHighlights();
    localStorage.removeItem(STEP_KEY);
    localStorage.removeItem(ACTIVE_KEY);
    if (dontShow.checked) {
      localStorage.setItem(TUTO_KEY, '1');
    }
    isTransitioning = false;
  }

  function findStartingStep() {
    var storedStep = localStorage.getItem(STEP_KEY);
    var storedActive = localStorage.getItem(ACTIVE_KEY);

    if (storedActive === '1' && storedStep !== null) {
      var idx = parseInt(storedStep, 10);
      if (!isNaN(idx) && idx >= 0 && idx < steps.length) {
        return idx;
      }
    }

    var page = currentPage();
    for (var i = 0; i < steps.length; i++) {
      if (steps[i].page === page || steps[i].page === 'any') {
        return i;
      }
    }
    return 0;
  }

  if (btnNext) btnNext.addEventListener('click', nextStep);
  if (btnPrev) btnPrev.addEventListener('click', prevStep);
  if (btnSkip) btnSkip.addEventListener('click', endTutorial);

  var relaunch = document.getElementById('adminTutoRelaunch');
  if (relaunch) {
    relaunch.addEventListener('click', function(e) {
      e.preventDefault();
      localStorage.removeItem(STEP_KEY);
      localStorage.setItem(ACTIVE_KEY, '1');
      showStep(0);
    });
  }

  var storedActive = localStorage.getItem(ACTIVE_KEY);
  var tutoDone = localStorage.getItem(TUTO_KEY);

  if (storedActive === '1') {
    var startIdx = findStartingStep();
    setTimeout(function() { showStep(startIdx); }, 400);
  } else if (!tutoDone) {
    setTimeout(function() { showStep(0); }, 600);
  }
})();