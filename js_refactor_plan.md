# Plan de Refactoring JavaScript — A.N.A.N.A.S.

## Diagnostic

### Problèmes identifiés

| # | Problème | Fichier(s) | Impact |
|---|----------|------------|--------|
| 1 | **`gallery.js` multifonctions** (238 lignes) — Galerie inline, modal plein écran, copy magnet, et star rating mélangés dans un seul fichier sans découpage fonctionnel | `gallery.js` | Maintenance difficile, risque d'effets de bord |
| 2 | **`var` partout au lieu de `let`/`const`** — Dans tous les fichiers JS, comportement de hoisting imprévisible, non-ES6+ | Tous les fichiers | Code quality |
| 3 | **Aucun module pattern / IIFE** — `initInlineGallery()` et `initImageModal()` sont des fonctions globales dans `gallery.js` | `gallery.js` | Pollution du scope global, collisions potentielles |
| 4 | **Copie clipboard dupliquée** — Logique similaire dans `main.js:42-58` (email) et `gallery.js:194-207` (magnet), sans abstraction partagée, gestion d'erreurs incohérente | `main.js`, `gallery.js` | Duplication, incohérence UX |
| 5 | **`alert()` bloquante** dans la recherche (`main.js:26`) | `main.js` | Mauvaise UX |
| 6 | **3 `DOMContentLoaded` indépendants** — Un par fichier JS, exécutés séparément sans orchestration | Tous les fichiers | Risque d'ordre d'exécution, difficile à maintenir |

### Ce qui est déjà bon

- `catalogue.js` (21 lignes) est court et bien structuré
- Aucune dépendance externe (vanilla JS pur)
- Séparation logique des responsabilités entre les fichiers : main = global, catalogue = catalogue, gallery = galerie
- Utilisation de `preventDefault()`, `aria-expanded`, événements clavier/touch dans la modal

---

## Options identifiées

### Option A — Refactoring léger (conservateur)
- Remplacer `var` → `const`/`let` partout
- Encapsuler `gallery.js` dans une IIFE/module
- Extraire la fonction clipboard en utility partagée
- Supprimer le `alert()` de recherche
- Sans changement de structure de fichiers

### Option B — Refactoring + modularisation (recommandé)
- Tout ce qui précède, plus :
- Découper `gallery.js` en 4 modules séparés
- Créer `utils/clipboard.js` pour la logique de copie partagée
- Regrouper les initialisations dans un seul point d'entrée `app.js`
- Nommer les modules avec module pattern (IIFE) sans bundler

### Option C — Refactoring complet avec outils modernes
- Ajouter TypeScript + Vite/Rollup
- ESLint + Prettier + tests unitaires
- **Hors scope** — surdimensionné pour un projet sans framework JS

> **Recommandation : Option B.** Elle adresse tous les problèmes identifiés sans introduire de dépendances build-tool, tout en rendant le code beaucoup plus maintenable.

---

## Plan détaillé (Option B)

### Phase 1 — Utility partagé clipboard

**Nouveau fichier :** `static/js/utils/clipboard.js`

- Extraire la logique de copie avec feedback (`main.js:42-58`) en fonction réutilisable :
  ```js
  copyText(element, successMsg, duration)
  ```
- Gère les erreurs clipboard uniformément (try/catch + feedback visuel)
- Utilisée par `main.js` (copie email) et `gallery.js` (copie magnet links)
- IIFE pour encapsuler du scope

### Phase 2 — Découpage de `gallery.js` en 4 modules

**Fichier :** `static/js/gallery/inlineGallery.js` (~35 lignes)
- Contenu actuel : `initInlineGallery()` (`gallery.js:10-35`)
- Gestion du clic sur les thumbnails → changement de la image principale avec transition opacity

**Fichier :** `static/js/gallery/imageModal.js` (~140 lignes)
- Contenu actuel : `initImageModal()` (`gallery.js:40-183`)
- Modal plein écran avec navigation (précédent/suivant), keyboard (Escape, Arrows), touch swipe, thumbnails actifs
- Réduction de complexité via fonctions helper locales

**Fichier :** `static/js/gallery/copyMagnet.js` (~15 lignes)
- Contenu actuel : copy magnet buttons (`gallery.js:194-207`)
- Utilise l'utility clipboard partagée au lieu du code dupliqué
- data-magnet → copie presse-papier + feedback "Copié !"

**Fichier :** `static/js/gallery/starRating.js` (~27 lignes)
- Contenu actuel : star rating hover + auto-submit (`gallery.js:209-236`)
- Hover highlight sur étoiles, submission automatique au clic
- Séparation claire de la responsabilité

### Phase 3 — Point d'entrée unique

**Nouveau fichier :** `static/js/app.js`

- Unique handler `DOMContentLoaded`
- Importe et initialise tous les modules dans l'ordre :
  1. `initCopyBtn()` (de main.js)
  2. `validatePasswordMatch()` (de main.js)
  3. `initSearch()` (de main.js — avec feedback amélioré sans alert)
  4. `initCatalogue()` (de catalogue.js)
  5. `initInlineGallery()` (gallery/inlineGallery.js)
  6. `initImageModal()` (gallery/imageModal.js)
  7. `initCopyMagnet()` (gallery/copyMagnet.js)
  8. `initStarRating()` (gallery/starRating.js)
- Orchestration centralisée, ordre déterministe

### Phase 4 — Nettoyage des fichiers existants

**Fichier :** `static/js/main.js` (réduit à ~50 lignes propres)
- Suppression de la duplication clipboard → utilise l'utility partagée
- Remplacement du `alert()` par feedback non-bloquant (toast inline ou feedback visuel sur le formulaire)
- Remplacement `var` → `const`/`let`
- IIFE pour encapsuler les fonctions globales

**Fichier :** `static/js/catalogue.js` (~21 lignes, pas de changement structurel majeur)
- Remplacement `var` → `const`/`let`
- Linting basique du style existant

---

## Arborescence résultante

```
static/js/
├── app.js                  # Point d'entrée unique — orchestre tous les modules (Phase 3)
├── utils/
│   └── clipboard.js        # Utility copy texte avec feedback réutilisable (Phase 1)
├── gallery/
│   ├── inlineGallery.js    # Galerie inline (strips de thumbnails) (Phase 2)
│   ├── imageModal.js       # Modal plein écran avec navigation (Phase 2)
│   ├── copyMagnet.js       # Boutons copy magnet links (Phase 2)
│   └── starRating.js       # Système de notation étoiles (Phase 2)
├── catalogue.js            # Expand/collapse catalogue — nettoyage var→const/let (Phase 4)
└── main.js                 # Recherche, copier email, validation mots de passe — nettoyé (Phase 4)
```

---

## Mise à jour des templates

**Fichier :** `templates/base.html` ou les templates spécifiques concernés

Remplacer les balises `<script src="..."> existantes par :

```html
<!-- Avant -->
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
<script src="{{ url_for('static', filename='js/catalogue.js') }}"></script>
<script src="{{ url_for('static', filename='js/gallery.js') }}"></script>

<!-- Après -->
<script src="{{ url_for('static', filename='js/utils/clipboard.js') }}"></script>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
```

Ou charger les modules individuellement si le chargement différé est nécessaire :

```html
<script src="{{ url_for('static', filename='js/utils/clipboard.js') }}"></script>
<script src="{{ url_for('static', filename='js/gallery/inlineGallery.js') }}"></script>
<script src="{{ url_for('static', filename='js/gallery/imageModal.js') }}"></script>
<script src="{{ url_for('static', filename='js/gallery/copyMagnet.js') }}"></script>
<script src="{{ url_for('static', filename='js/gallery/starRating.js') }}"></script>
```

---

## Estimation du travail

| Phase | Description | Effort estimé | Risque |
|-------|-------------|---------------|--------|
| Phase 1 | `utils/clipboard.js` — extraction utility | 15 min | Faible — extraction pure sans impact |
| Phase 2 | Découpage `gallery.js` en 4 modules | 45 min | Moyen — vérifier que les IDs DOM n'entrent pas en conflit entre modules |
| Phase 3 | `app.js` entry point — orchestration | 10 min | Faible |
| Phase 4 | Nettoyage `main.js` + `catalogue.js` | 20 min | Faible — `catalogue.js` minimal, `main.js` straightforward |
| Phase 5 | Mise à jour templates HTML | 15 min | Moyen — vérifier l'ordre de chargement et la présence de tous les éléments DOM |

**Total estimé : ~2h**

---

## Notes

- Le refactoring ne change **aucun comportement fonctionnel** — uniquement la structure du code
- `catalogue.js` est déjà court et propre → pas de refactoring structurel nécessaire, juste modernisation `var` → `const`/`let`
- Les IIFEs garantissent l'encapsulation sans nécessiter de module system (compatibilité navigateurs existante)
- Aucune dépendance externe ajoutée
