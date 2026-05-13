# Plan d'Actions — Restructuration HTML A.N.A.N.A.S.

## Points forts existants

- Héritage de templates cohérent : `base.html` → page templates → partials
- Balises sémantiques utilisées correctement (`main`, `section`, `nav`, `aside`)
- Partials bien extraits pour header/footer
- Pattern blocks Jinja2 standardisé (`title`, `meta_description`, `content`, `extra_head`, `extra_scripts`)
- CSS modulaire sans préprocesseur (16 modules importés dans `style.css`)

---

## Problèmes identifiés

| # | Problème | Fichier(s) | Sévérité | Impact |
|---|----------|------------|----------|--------|
| 1 | Pas de bloc flash messages / erreurs | Tous les templates | Élevée | Impossible d'afficher succès/erreurs (inscription, connexion, commentaires) |
| 2 | Formulaires POST sans CSRF token | `connexion.html:15`, `inscription.html:15`, `item_detail.html:211` | Élevée | Flask-WTF configuré mais formulaires inutilisables en production |
| 3 | Styles inline dans `gallery.html` | `gallery.html:17,20-36` | Moyenne | Violation CSS modulaire |
| 4 | Modal image dupliquée | `item_detail.html:250-273`, `gallery.html:20-34` | Moyenne | Code dupliqué, comportement différent entre les deux pages |
| 5 | Containers imbriqués inutiles | `item_detail.html:128,164,191`, `gallery.html:10` | Faible | Sur-nesting, complexité visuelle |
| 6 | Banderolle non sémantique | `item_detail.html:20-25` | Moyenne | "Aperçu/Donnée/Visualisation" sans comportement défini ni CSS associé |
| 7 | Images catalogue `alt=""` | `catalogue.html:28` | Faible | Accessibilité (WCAG 2.1) |
| 8 | Formulaire recherche `action="#"` | `header.html:24` | Faible | Ne dirige vers aucune route réelle |

---

## Étapes à suivre

### Étape 1 — Ajouter les flash messages dans `base.html`

**Fichier :** `templates/base.html`

Ajouter après `{% include 'partials/header.html' %}` :

```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash-container" role="alert">
      {% for category, message in messages %}
        <div class="flash flash-{{ category }}">{{ message }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

**Fichier :** `static/css/base.css` — ajouter à la fin :

```css
.flash-container { position: relative; z-index: 1000; }
.flash { padding: 0.75rem 1rem; margin: 0.5rem auto; max-width: 600px; border-radius: 4px; text-align: center; }
.flash-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.flash-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.flash-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
```

**Fichiers modifiés :** `base.css`, `base.html` — **2 fichiers**
**Effort estimé :** 15 min | **Risque :** Faible

---

### Étape 2 — Ajouter CSRF token aux formulaires POST

**Fichiers :** `connexion.html:15`, `inscription.html:15`, `item_detail.html:211`

Après chaque balise `<form ...>`, ajouter :

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

**Exemple — `connexion.html` ligne 15 :**

```html
<form class="auth-form" id="connexionForm" action="/connexion" method="POST">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
  ...
</form>
```

**Fichiers modifiés :** `connexion.html`, `inscription.html`, `item_detail.html` — **3 fichiers**
**Effort estimé :** 10 min | **Risque :** Faible

---

### Étape 3 — Extraire la modal image en partial réutilisable

Créer un nouveau partial `templates/partials/image_modal.html` :

```html
<!-- Modal image (réutilisable) -->
<div class="image-modal" id="imageModal">
  <div class="modal-backdrop"></div>
  <div class="modal-content white-box">
    <button class="modal-close" aria-label="Fermer">&#10005;</button>
    <div class="modal-left">
      <button class="modal-nav modal-prev" aria-label="Précédent">&#8249;</button>
      <img class="modal-img" src="" alt="">
      <button class="modal-nav modal-next" aria-label="Suivant">&#8250;</button>
    </div>
    <div class="modal-thumbnails">
      {% block modal_thumbnails %}{% endblock %}
    </div>
  </div>
</div>
```

**Dans `item_detail.html` :** remplacer les lignes 249-273 par :

```html
{% include 'partials/image_modal.html' %}
```

**Dans `gallery.html` :** adapter le bloc thumbnails pour injecter les miniatures de galerie via un block `{% block modal_thumbnails %}`.

**Fichiers modifiés :** `partials/image_modal.html` (créé), `item_detail.html`, `gallery.html` — **3 fichiers**
**Effort estimé :** 20 min | **Risque :** Moyen — tester les deux pages après modification

---

### Étape 4 — Nettoyer `gallery.html` — supprimer styles inline

**Fichier :** `templates/gallery.html`

Remplacer ligne 17 :

```html
<!-- AVANT -->
<section style="display:flex;align-items:center;gap:0.75rem;padding:1.5rem 0;">

<!-- APRÈS -->
<section class="gallery-backbar">
  <a href="/catalogue/item/{{ item.id }}" class="gallery-back-link">
    &larr; Retour à la fiche
  </a>
</section>
```

Supprimer également les styles inline sur lignes 20 et 36. Ajouter dans `static/css/features/gallery-modal.css` :

```css
.gallery-backbar { display: flex; align-items: center; padding: 1.5rem 0; }
.gallery-back-link { color: var(--specs-gray); text-decoration: none; font-size: 0.9rem; }
```

**Fichiers modifiés :** `gallery.html`, `gallery-modal.css` — **2 fichiers**
**Effort estimé :** 15 min | **Risque :** Faible

---

### Étape 5 — Nettoyer les containers imbriqués dans `item_detail.html`

**Fichier :** `templates/item_detail.html`

Lignes 128, 164, 191 : supprimer `<div class="container">` inutile à l'intérieur de `detail-body` qui contient déjà un `.container` :

```html
<!-- AVANT ligne 128 -->
<section class="tech-section">
  <div class="container">
    <h2>Spécifications techniques</h2>

<!-- APRÈS -->
<section class="tech-section">
  <h2>Spécifications techniques</h2>
```

Même nettoyage lignes 164 et 191 (sections "Réutilisation" et "Commentaires").

**Fichiers modifiés :** `item_detail.html` — **1 fichier**
**Effort estimé :** 10 min | **Risque :** Faible

---

### Étape 6 — Remplacer la bandelette par un nav sémantique

**Fichier :** `templates/item_detail.html` lignes 20-25

```html
<!-- AVANT -->
<div class="banderolle">
  <div class="banderolle-spacer"></div>
  <a href="#" class="btn-band apercu-btn">Aperçu</a>
  <a href="#" class="btn-band donnee-btn">Donnée</a>
  <a href="#" class="btn-band visu-btn">Visualisation</a>
</div>

<!-- APRÈS -->
<nav class="detail-tabs" aria-label="Actions sur la donnée">
  <a href="#" class="tab-btn active">Aperçu</a>
  <a href="/catalogue/item/{{ item.id }}/gallery" class="tab-btn">Visualisation</a>
  <a href="{{ item.magnet }}" class="btn-download tab-btn" target="_blank">Télécharger</a>
</nav>
```

Ajouter dans `static/css/features/product.css` (ou un nouveau fichier) :

```css
.detail-tabs { display: flex; gap: 0.5rem; padding: 1rem 0; }
.tab-btn { padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; }
.tab-btn.active { background: var(--primary-color); color: #fff; }
.tab-btn:hover { opacity: 0.85; }
```

**Fichiers modifiés :** `item_detail.html`, CSS associé — **2 fichiers**
**Effort estimé :** 15 min | **Risque :** Faible

---

### Étape 7 — Texte alt descriptif et action formulaire de recherche

**Fichier :** `templates/catalogue.html` ligne 28 :

```html
<!-- AVANT -->
<img class="catalogue-image" src="{{ item.image }}" alt="" loading="lazy">

<!-- APRÈS -->
<img class="catalogue-image" src="{{ item.image }}" alt="{{ item.title }}" loading="lazy">
```

**Fichier :** `templates/header.html` ligne 24 :

```html
<!-- AVANT -->
<form class="search-bar" role="search" action="#" method="get">

<!-- APRÈS -->
<form class="search-bar" role="search" action="/catalogue" method="get">
  <label class="sr-only" for="site-search">Rechercher dans le catalogue</label>
```

**Fichiers modifiés :** `catalogue.html`, `header.html` — **2 fichiers**
**Effort estimé :** 5 min | **Risque :** Aucun

---

### Étape 8 — Extraire la pagination en partial réutilisable (optionnel)

Créer `templates/partials/pagination.html` :

```html
<nav class="pagination" aria-label="Pagination">
  {% if page > 1 %}
    <a class="btn btn-outline pagination-prev" href="{{ base_url }}/{{ page - 1 }}">&#9664; Précédent</a>
  {% else %}
    <span class="btn btn-outline pagination-prev disabled">&#9664; Précédent</span>
  {% endif %}

  <div class="pagination-numbers">
    {% for p in page_numbers %}
      {% if p == '...' %}
        <span class="pagination-ellipsis">&hellip;</span>
      {% elif p == page %}
        <span class="pagination-link active">{{ p }}</span>
      {% else %}
        <a class="pagination-link" href="{{ base_url }}/{{ p }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
  </div>

  {% if page < total_pages %}
    <a class="btn btn-outline pagination-next" href="{{ base_url }}/{{ page + 1 }}">Suivant &#9668;</a>
  {% else %}
    <span class="btn btn-outline pagination-next disabled">Suivant &#9668;</span>
  {% endif %}
</nav>
```

**Fichier :** `templates/catalogue.html` — remplacer la ligne 52-78 par :

```html
{% if total_pages > 1 %}
  {% set pag = { 'base_url': '/catalogue', 'page': page, 'total_pages': total_pages, 'page_numbers': page_numbers } %}
  {% include 'partials/pagination.html' %}
{% endif %}
```

**Fichiers modifiés :** `partials/pagination.html` (créé), `catalogue.html` — **2 fichiers**
**Effort estimé :** 20 min | **Risque :** Faible

---

### Étape 9 — Extraire les sections de la page d'accueil en partials (optionnel)

`index.html` contient 404 lignes. Décomposer en partials :

```
templates/partials/index_sections/
├── hero.html              ← Hero section (lignes 9-46)
├── gp_packs.html          ← GeoPackage packs (lignes 48-139)
├── di_data.html           ← Données individuelles (lignes 141-234)
├── p2p_section.html       ← Peer-to-Peer (lignes 236-372)
└── mirrors.html           ← Sites miroirs (lignes 373-401)
```

`index.html` réduit à ~50 lignes :

```html
{% extends 'base.html' %}
{% block title %}{{ title }}{% endblock %}
{% block meta_description %}{{ meta_description }}{% endblock %}
{% block content %}
<main>
  {% include 'partials/index_sections/hero.html' %}
  {% include 'partials/index_sections/gp_packs.html' %}
  {% include 'partials/index_sections/di_data.html' %}
  {% include 'partials/index_sections/p2p_section.html' %}
  {% include 'partials/index_sections/mirrors.html' %}
</main>
{% endblock %}
```

**Fichiers modifiés :** `partials/index_sections/` (5 nouveaux fichiers), `index.html` — **6 fichiers**
**Effort estimé :** 40 min | **Risque :** Faible — isolated, n'affecte pas les autres pages

---

## Arborescence cible finale

```
templates/
├── base.html                    ← Étape 1 : + flash messages
├── index.html                   ← Étape 9 (optionnel) : sections décomposées
├── catalogue.html               ← Étape 7 + Étape 8
├── item_detail.html             ← Étape 2, 3, 5, 6
├── gallery.html                 ← Étape 3, 4
├── connexion.html               ← Étape 2
├── inscription.html             ← Étape 2
├── contact.html                 ← pas de changement
└── partials/
    ├── header.html              ← Étape 7 : action formulaire corrigée
    ├── footer.html              ← pas de changement
    ├── image_modal.html         ← Étape 3 : NOUVEAU — modal partagée
    └── pagination.html          ← Étape 8 : NOUVEAU — pagination réutilisable
    └── index_sections/          ← Étape 9 (optionnel) : NOUVEAU répertoire
        ├── hero.html
        ├── gp_packs.html
        ├── di_data.html
        ├── p2p_section.html
        └── mirrors.html

static/css/
├── base.css                     ← Étape 1 : + flash styles
├── features/
│   ├── gallery-modal.css        ← Étape 4 : + .gallery-backbar
│   └── product.css              ← Étape 6 : + .detail-tabs, .tab-btn
```

---

## Récapitulatif effort total

| Étape | Description | Effort | Risque | Obligation |
|-------|-------------|--------|--------|------------|
| 1 | Flash messages dans `base.html` | 15 min | Faible | Obligatoire |
| 2 | CSRF token formulaires POST | 10 min | Faible | Obligatoire |
| 3 | Modal image → partial partagé | 20 min | Moyen | Recommandé |
| 4 | Styles inline gallery.html | 15 min | Faible | Recommandé |
| 5 | Containers imbriqués cleanup | 10 min | Faible | Recommandé |
| 6 | Banderolle → nav sémantique | 15 min | Faible | Recommandé |
| 7 | Alt text + action recherche | 5 min | Aucun | Recommandé |
| 8 | Pagination → partial (optionnel) | 20 min | Faible | Optionnel |
| 9 | index.html → sections partials (optionnel) | 40 min | Faible | Optionnel |
| **Total obligatoire** | Étapes 1-7 | **~1h 30min** | | |
| **Total complet** | + Étape 8-9 | **+1h 30min** | | |

---

## Ordre d'exécution recommandé

Les étapes sont déjà ordonnées par dépendance (de la plus critique à l'optionnel). À exécuter dans l'ordre 1 → 7 pour le minimum fonctionnel, puis 8-9 si nécessaire.

Tester après chaque étape :
- `./setup.sh local && ./run.sh` → port 5000
- Vérifier mobile (680px) et tablette (980px) — voir `responsive.css`
- Respecter la charte graphique (`charte_graphique_m2.pdf`)

---

## Notes

- Les formulaires POST qui recevront des handlers (connexion, inscription, commentaires) bénéficieront directement du bloc flash messages (Étape 1) + CSRF token (Étape 2)
- L'ordre 1 → 7 peut être fait en une seule session de travail (~1h 30min)
- Les étapes optionnelles (8-9) sont isolées et peuvent être faites séparément
