(function() {
  const TUTO_KEY = 'admin_panel_tuto_v5';
  const STEP_KEY = 'admin_panel_tuto_step_v5';
  const ACTIVE_KEY = 'admin_panel_tuto_active_v5';

  function currentPage() {
    var p = window.location.pathname;
    if (p.startsWith('/admin/reports')) return 'reports';
    if (p.startsWith('/admin/moderation')) return 'moderation';
    if (p.startsWith('/admin/contact-messages')) return 'contact-messages';
    if (p.startsWith('/admin/mirrors')) return 'mirrors';
    if (p.startsWith('/admin/featured')) return 'featured';
    if (p.startsWith('/admin/audit')) return 'audit';
    return 'users';
  }

  var steps = [
    {
      page: 'any',
      target: '.admin-nav',
      position: 'bottom',
      text: '<strong>Navigation d\'administration</strong> — Cette barre donne accès aux 7 sections du panneau. Cliquez sur <strong>Suivant</strong> pour découvrir chaque section.',
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
      text: '<strong>Liste des utilisateurs</strong> — Chaque ligne affiche l\'ID, le nom, l\'email et le statut. Les boutons <strong>Bannir/Débannir</strong> permettent de contrôler l\'accès au site.',
    },
    {
      page: 'users',
      target: '.admin-nav a:nth-child(2)',
      position: 'bottom',
      navigateTo: '/admin/reports',
      text: '<strong>Signalements</strong> — Traitez les signalements de contenu inapproprié envoyés par les utilisateurs.',
    },
    {
      page: 'reports',
      target: '#report-status-filters, #reports-table',
      position: 'top',
      text: '<strong>Signalements</strong> — Filtrez par statut (<strong>En attente</strong>, <strong>Résolu</strong>, <strong>Non fondé</strong>). Chaque signalement peut être marqué comme résolu ou rejeté.',
    },
    {
      page: 'reports',
      target: '.admin-nav a:nth-child(3)',
      position: 'bottom',
      navigateTo: '/admin/moderation',
      text: '<strong>Modération</strong> — Modérez les commentaires et les publications du catalogue.',
    },
    {
      page: 'moderation',
      target: '.mod-tabs',
      position: 'top',
      text: '<strong>Modération</strong> — Deux onglets : <strong>Commentaires</strong> et <strong>Cartes, Applications &amp; Données</strong>. Supprimez, vérifiez ou retirez la vérification du contenu.',
    },
    {
      page: 'moderation',
      target: '.admin-nav a:nth-child(4)',
      position: 'bottom',
      navigateTo: '/admin/contact-messages',
      text: '<strong>Messages</strong> — Consultez les messages envoyés par les visiteurs via la page de contact.',
    },
    {
      page: 'contact-messages',
      target: '#contact-msg-filters, #contact-msgs-table',
      position: 'top',
      text: '<strong>Messages de contact</strong> — Filtrez par statut (<strong>Tous</strong>, <strong>Non lus</strong>, <strong>Lus</strong>). Cliquez sur <strong>Voir</strong> pour lire le message complet, ou <strong>Supprimer</strong> pour l\'effacer.',
    },
    {
      page: 'contact-messages',
      target: '.admin-nav a:nth-child(5)',
      position: 'bottom',
      navigateTo: '/admin/mirrors',
      text: '<strong>Sites miroirs</strong> — Ajoutez, modifiez ou supprimez les sites miroirs affichés sur la page d\'accueil.',
    },
    {
      page: 'mirrors',
      target: '#mirrors-table, .mirrors-header',
      position: 'top',
      text: '<strong>Sites miroirs</strong> — Gérez les liens affichés dans la section « Sites miroirs » de la page d\'accueil. <strong>Ajoutez</strong> un nouveau miroir, <strong>modifiez</strong> ou <strong>supprimez</strong> un miroir existant.',
    },
    {
      page: 'mirrors',
      target: '.admin-nav a:nth-child(6)',
      position: 'bottom',
      navigateTo: '/admin/featured',
      text: '<strong>Données en avant</strong> — Choisissez les items du catalogue à afficher dans la section « Exemples de Données » de la page d\'accueil.',
    },
    {
      page: 'featured',
      target: '#featured-table, .mirrors-header',
      position: 'top',
      text: '<strong>Données en avant</strong> — Recherchez un item du catalogue et ajoutez-le à la section « Exemples de Données Disponibles » de la page d\'accueil. Activez ou retirez les données facilement.',
    },
    {
      page: 'featured',
      target: '.admin-nav a:nth-child(7)',
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