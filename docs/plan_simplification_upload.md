# Plan : Simplification de la page Upload

## Problèmes

1. **Dropdown "Niveau de granularité"** impose un choix "Pack" vs "Fichier individuel" peu intuitif — les deux sections magnet s'excluent.
2. **Select "zoom"** oblige à ouvrir un menu déroulant pour chaque magnet, lent quand on en a beaucoup.
3. **Pas de mode bulk** — ajouter 10+ magnets un par un est fastidieux.
4. **Trop de show/hide conditionnels** entre type, granularité, format, textarea CSV — l'utilisateur voit des champs apparaître/disparaître.

## Solution en 7 volets

---

### Volet 0 — Tutoriel / Visite guidée de la page Upload

Un overlay de prise en main qui guide l'utilisateur à travers chaque section du formulaire avant qu'il ne commence à le remplir. Le tutoriel se déclenche automatiquement au premier affichage de la page, avec une option "Ne plus afficher".

#### Déclenchement

Stocké en `localStorage` :

```javascript
const TUTO_KEY = 'upload_tuto_done_v2';
const tutoDone = localStorage.getItem(TUTO_KEY);

if (!tutoDone) {
  startTutorial();
}
```

Réinitialisable via un lien discret "Guide" en haut de la page pour le relancer manuellement.

#### Étapes du tutoriel

Le tutoriel met en évidence chaque bloc du formulaire un par un avec un tooltip positionné à côté :

| Étape | Cible | Texte |
|---|---|---|
| 1 | `#title` | **Titre** — Donnez un nom à votre publication. C'est le titre visible dans le catalogue. |
| 2 | `#type` + `#format_type` | **Type et format** — Choisissez la catégorie (géodonnées, carte, application) et le format technique du fichier. |
| 3 | `#magnetSection` | **Les données** — Collez un aperçu CSV (optionnel) et ajoutez vos liens Magnet. Le bouton **+** ajoute un lien, **Ajouter en lot** permet d'en coller plusieurs d'un coup. |
| 4 | `.zoom-pills` | **Niveau de zoom** — Pour chaque lien Magnet, cliquez sur le niveau géographique : IRIS, Communes, Départements, Régions ou Pays. |
| 5 | `#imageMagnetEntries` | **Images** — Optionnel. Ajoutez des liens Magnet pointant vers des images (PNG, JPG...). Elles seront téléchargées automatiquement par le serveur. |
| 6 | `.upload-actions` | **Publier ou brouillon** — **Publier** rend votre contenu visible. **Brouillon** le sauvegarde pour le finir plus tard. |

#### Template : structure du tutoriel

```html
<!-- Overlay semi-transparent derrière le tooltip -->
<div id="tutoOverlay" class="tuto-overlay hidden-section"></div>

<!-- Tooltip du tutoriel -->
<div id="tutoTooltip" class="tuto-tooltip hidden-section">
  <div class="tuto-step-indicator">
    <span id="tutoStepCurrent">1</span>/<span id="tutoStepTotal">6</span>
  </div>
  <p id="tutoStepText"></p>
  <div class="tuto-actions">
    <button type="button" class="btn btn-sm btn-outline" id="tutoPrev">← Précédent</button>
    <button type="button" class="btn btn-sm btn-primary" id="tutoNext">Suivant →</button>
    <button type="button" class="btn btn-sm btn-outline" id="tutoSkip">Passer</button>
  </div>
  <label class="tuto-dont-show">
    <input type="checkbox" id="tutoDontShow" />
    Ne plus afficher ce guide
  </label>
</div>
```

#### CSS

```css
.tuto-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  z-index: 999;
}

.tuto-overlay.hidden-section,
.tuto-tooltip.hidden-section {
  display: none !important;
}

.tuto-tooltip {
  position: absolute;
  z-index: 1000;
  background: var(--charcoal);
  color: var(--white);
  border-radius: 10px;
  padding: 1.25rem;
  max-width: 340px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.3);
  animation: tutoFadeIn 0.2s ease;
}

@keyframes tutoFadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.tuto-tooltip::after {
  content: '';
  position: absolute;
  border: 8px solid transparent;
}

/* Flèche selon position */
.tuto-tooltip.pos-bottom::after {
  top: -16px;
  left: 24px;
  border-bottom-color: var(--charcoal);
}
.tuto-tooltip.pos-top::after {
  bottom: -16px;
  left: 24px;
  border-top-color: var(--charcoal);
}
.tuto-tooltip.pos-right::after {
  left: -16px;
  top: 24px;
  border-right-color: var(--charcoal);
}
.tuto-tooltip.pos-left::after {
  right: -16px;
  top: 24px;
  border-left-color: var(--charcoal);
}

.tuto-step-indicator {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.5);
  margin-bottom: 0.5rem;
}

.tuto-step-indicator span {
  color: var(--mustard);
  font-weight: 700;
  font-size: 1rem;
}

.tuto-tooltip p {
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0 0 1rem;
}

.tuto-tooltip strong {
  color: var(--mustard);
}

.tuto-actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.tuto-actions .btn {
  font-size: 0.8rem;
  padding: 0.4rem 0.75rem;
}

.tuto-actions .btn-outline {
  border-color: rgba(255,255,255,0.3);
  color: var(--white);
}

.tuto-actions .btn-outline:hover {
  border-color: var(--white);
  background: rgba(255,255,255,0.1);
}

.tuto-dont-show {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: rgba(255,255,255,0.5);
  cursor: pointer;
}

.tuto-dont-show input {
  accent-color: var(--mustard);
}

/* Cible mise en surbrillance */
.tuto-highlight {
  position: relative;
  z-index: 1001 !important;
  box-shadow: 0 0 0 4px var(--mustard), 0 0 24px rgba(212, 175, 55, 0.4);
  border-radius: 8px;
  transition: box-shadow 0.2s ease;
}

.tuto-relaunch {
  font-size: 0.85rem;
  color: var(--forest);
  text-decoration: underline;
  cursor: pointer;
}
```

#### JS : logique du tutoriel

```javascript
// static/js/upload_tuto.js — chargé sur la page upload

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
  ];

  let currentStep = 0;

  const overlay = document.getElementById('tutoOverlay');
  const tooltip = document.getElementById('tutoTooltip');
  const stepCur = document.getElementById('tutoStepCurrent');
  const stepTotal = document.getElementById('tutoStepTotal');
  const stepText = document.getElementById('tutoStepText');
  const btnPrev = document.getElementById('tutoPrev');
  const btnNext = document.getElementById('tutoNext');
  const btnSkip = document.getElementById('tutoSkip');
  const dontShow = document.getElementById('tutoDontShow');

  if (stepTotal) stepTotal.textContent = steps.length;

  function positionTooltip(targetEl) {
    const rect = targetEl.getBoundingClientRect();
    const step = steps[currentStep];
    const ttipW = 340;

    let top, left;
    if (step.position === 'bottom') {
      top = rect.bottom + 12;
      left = rect.left + rect.width / 2 - ttipW / 2;
    } else if (step.position === 'top') {
      top = rect.top - tooltip.offsetHeight - 12;
      left = rect.left + rect.width / 2 - ttipW / 2;
    } else if (step.position === 'right') {
      top = rect.top + rect.height / 2 - tooltip.offsetHeight / 2;
      left = rect.right + 12;
    } else {
      top = rect.top + rect.height / 2 - tooltip.offsetHeight / 2;
      left = rect.left - ttipW - 12;
    }

    // Garder dans le viewport
    top = Math.max(10, Math.min(top, window.innerHeight - tooltip.offsetHeight - 10));
    left = Math.max(10, Math.min(left, window.innerWidth - ttipW - 10));

    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
  }

  function showStep(index) {
    if (index < 0) index = 0;
    if (index >= steps.length) { endTutorial(); return; }
    currentStep = index;

    document.querySelectorAll('.tuto-highlight').forEach(el => el.classList.remove('tuto-highlight'));

    const step = steps[index];
    const target = document.querySelector(step.target);
    if (!target) { showStep(index + 1); return; }

    target.classList.add('tuto-highlight');
    tooltip.className = 'tuto-tooltip pos-' + step.position;
    stepCur.textContent = index + 1;
    stepText.innerHTML = step.text;

    overlay.classList.remove('hidden-section');
    tooltip.classList.remove('hidden-section');

    target.scrollIntoView({ behavior: 'smooth', block: 'center' });

    btnPrev.style.visibility = index === 0 ? 'hidden' : 'visible';
    btnNext.textContent = index === steps.length - 1 ? 'Terminer ✓' : 'Suivant →';

    positionTooltip(target);
  }

  function endTutorial() {
    overlay.classList.add('hidden-section');
    tooltip.classList.add('hidden-section');
    document.querySelectorAll('.tuto-highlight').forEach(el => el.classList.remove('tuto-highlight'));
    if (dontShow.checked) {
      localStorage.setItem(TUTO_KEY, '1');
    }
  }

  btnNext.addEventListener('click', () => showStep(currentStep + 1));
  btnPrev.addEventListener('click', () => showStep(currentStep - 1));
  btnSkip.addEventListener('click', endTutorial);

  document.getElementById('relaunchTuto')?.addEventListener('click', (e) => {
    e.preventDefault();
    showStep(0);
  });

  // Déclenchement automatique au premier affichage
  if (!localStorage.getItem(TUTO_KEY)) {
    setTimeout(() => showStep(0), 600);
  }
})();
```

#### Lien "Guide" en haut de la page

```html
<div class="upload-header">
  <h1>Publier des données</h1>
  <p>Téléversez vos fichiers géospatiaux sur A.N.A.N.A.S. 
     <a href="#" id="relaunchTuto" class="tuto-relaunch">Guide</a>
  </p>
</div>
```

---

### Volet 1 — Supprimer le dropdown "Niveau de granularité"

Le mode pack/individual est déduit automatiquement côté JS :
- **1 seul magnet** → `data_format_level: "pack"`, magnet stocké dans `item.magnet_link`
- **2+ magnets** → `data_format_level: "individual"`, magnets stockés dans `item.metadata_json`

#### Template (`templates/users/upload.html`)

Supprimer le `<select id="data_format_level">` et ses conteneurs `packMagnetGroup` / `individualMagnetGroup`. Remplacer la section `#magnetSection` par :

```html
<div id="magnetSection">
  <div class="form-group">
    <label for="magnet_link_0" class="label-with-help">Liens Magnet <span class="help-icon" data-tooltip="...">?</span></label>
  </div>
  <div id="magnetEntries"></div>
  <div class="magnet-actions">
    <button type="button" class="btn btn-outline mt-10" id="addMagnetBtn">+ Ajouter un lien</button>
    <button type="button" class="btn btn-outline mt-10" id="bulkMagnetBtn">Ajouter en lot</button>
  </div>
  <div id="bulkMagnetGroup" class="hidden-section">
    <!-- zone bulk (volet 3) -->
  </div>
</div>
```

#### JS (`static/js/upload.js`)

- Supprimer `toggleMagnetSections()` et les références à `dataFormatLevel`, `packMagnetGroup`, `individualMagnetGroup`.
- Au chargement, créer automatiquement **une première entrée magnet** (toujours visible).
- Clic sur `+` → ajoute une nouvelle entrée.
- Clic sur `Supprimer` → supprime l'entrée (sauf s'il n'en reste qu'une).
- À la soumission, compter les magnets remplis → envoyer `data_format_level` et la bonne structure (`magnet_link` vs `magnet_links`).
- Pour `carte` et `application` : cacher le bouton `+` et `bulk` (garder seulement le champ unique).

#### Backend (`src/user_routes.py`)

Aucun changement nécessaire — les endpoints `/api/upload/file` et `/api/upload/item` supportent déjà les deux modes.

---

### Volet 2 — Remplacer le select "zoom" par des pills cliquables

Chaque entrée magnet affiche les 5 niveaux de zoom sous forme de boutons horizontaux.

```html
<div class="magnet-entry">
  <input type="text" name="magnet_link[]" placeholder="magnet:?xt=urn:btih:..." class="form-control" />
  <div class="zoom-pills">
    <button type="button" class="zoom-pill" data-zoom="iris">IRIS</button>
    <button type="button" class="zoom-pill" data-zoom="communes">Communes</button>
    <button type="button" class="zoom-pill" data-zoom="departements">Départements</button>
    <button type="button" class="zoom-pill active" data-zoom="regions">Régions</button>
    <button type="button" class="zoom-pill" data-zoom="pays">Pays</button>
  </div>
  <input type="hidden" name="zoom_level[]" value="regions" />
  <button type="button" class="btn btn-outline remove-magnet-btn">✕</button>
</div>
```

#### JS

- Délégation d'événement sur `.zoom-pill` → toggle `active`, met à jour le `<input type="hidden">` correspondant.
- Un seul pill actif à la fois par entrée.
- L'input hidden associé stocke la valeur pour l'envoi du formulaire.

#### CSS

```css
.zoom-pills {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.zoom-pill {
  padding: 4px 10px;
  font-size: 0.78rem;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--white);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.zoom-pill:hover {
  border-color: var(--mustard);
  background: rgba(212, 175, 55, 0.1);
}

.zoom-pill.active {
  background: var(--mustard);
  border-color: var(--mustard);
  color: var(--charcoal);
  font-weight: 600;
}
```

---

### Volet 3 — Ajout en lot (bulk)

Un bouton "Ajouter en lot" ouvre une zone de texte + un sélecteur de zoom commun.

```html
<div id="bulkMagnetGroup" class="hidden-section bulk-magnet-group">
  <div class="form-group">
    <label>Collez vos liens Magnet (1 par ligne)</label>
    <textarea id="bulkMagnetTextarea" rows="5" placeholder="magnet:?xt=urn:btih:abc123...&#10;magnet:?xt=urn:btih:def456...&#10;magnet:?xt=urn:btih:ghi789..."></textarea>
    <div class="bulk-magnet-footer">
      <span id="bulkMagnetCount" class="data-line-count">0 liens détectés</span>
    </div>
  </div>

  <div class="form-group">
    <label>Zoom pour tous ces liens</label>
    <div class="zoom-pills" id="bulkZoomPills">
      <button type="button" class="zoom-pill" data-zoom="iris">IRIS</button>
      <button type="button" class="zoom-pill" data-zoom="communes">Communes</button>
      <button type="button" class="zoom-pill active" data-zoom="departements">Départements</button>
      <button type="button" class="zoom-pill" data-zoom="regions">Régions</button>
      <button type="button" class="zoom-pill" data-zoom="pays">Pays</button>
    </div>
  </div>

  <div class="bulk-magnet-actions">
    <button type="button" class="btn btn-primary" id="bulkMagnetConfirm">Ajouter ces X liens</button>
    <button type="button" class="btn btn-outline" id="bulkMagnetCancel">Annuler</button>
  </div>
</div>
```

#### JS

- `input` sur le textarea → détecte les lignes non vides, met à jour le compteur.
- `#bulkMagnetConfirm` → pour chaque ligne, crée une entrée magnet avec le zoom sélectionné dans `#bulkZoomPills`, puis vide le textarea et referme la zone.
- `#bulkMagnetCancel` → vide et cache la zone.
- `#bulkMagnetBtn` → toggle show/hide de `#bulkMagnetGroup`.

#### CSS additionnel

```css
.bulk-magnet-group {
  background: var(--white);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 0.75rem;
}

.bulk-magnet-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.bulk-magnet-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.75rem;
}
```

---

### Volet 4 — Images via liens Magnet (téléchargement + cache serveur)

L'utilisateur peut fournir des liens Magnet pointant vers des images (PNG, JPG, WebP...). Le serveur télécharge ces images **une seule fois** depuis le réseau BitTorrent et les stocke en cache disque. Sur la page item, les images sont servies depuis le cache local, **mais les liens Magnet d'origine restent affichés** comme information technique.

#### Flux complet

```
Upload                    Serveur                        Page Item
------                    -------                        ---------
User colle magnet      →  Télécharge via libtorrent   →  Affiche l'image
d'une image                  ↓                            depuis le cache
                             Stocke dans
                             instance/image_cache/
                             ET garde le magnet
                             en base (ItemGallery.src
                             + magnet dans data_json)
                                                  →  Affiche le lien magnet
                                                     sous l'image en 
                                                     "Source / Lien Magnet"
```

#### Modèle de données

Pas de nouvelle table. On enrichit `ItemGallery` existante :

| Colonne | Valeur | Exemple |
|---|---|---|
| `media_type` | `"image"` | |
| `src` | Chemin du fichier cache | `/static/cache/img/abc123.png` |
| `data_json` | `{"magnet_link": "magnet:?...", "original_filename": "photo.png"}` | Magnet d'origine conservé |
| `label` | Nom affiché | `"Carte des départements"` |

#### Template upload : nouvelle section "Images"

Dans `templates/users/upload.html`, ajouter après la section "Données" :

```html
<div class="upload-section">
  <h2>Images (optionnel)</h2>
  <div class="form-group">
    <label class="label-with-help">Liens Magnet vers des images <span class="help-icon" data-tooltip="Collez un ou plusieurs liens Magnet pointant vers des images (PNG, JPG, WebP...). Les images seront téléchargées une fois et mises en cache sur le serveur. Les liens Magnet restent visibles sur la fiche.">?</span></label>
  </div>
  <div id="imageMagnetEntries"></div>
  <div class="magnet-actions">
    <button type="button" class="btn btn-outline" id="addImageMagnetBtn">+ Ajouter une image</button>
    <button type="button" class="btn btn-outline" id="bulkImageMagnetBtn">Ajouter en lot</button>
  </div>
  <div id="bulkImageMagnetGroup" class="hidden-section bulk-magnet-group">
    <div class="form-group">
      <label>Collez vos liens Magnet d'images (1 par ligne)</label>
      <textarea id="bulkImageTextarea" rows="5" placeholder="magnet:?xt=urn:btih:abc123...&#10;magnet:?xt=urn:btih:def456..."></textarea>
      <div class="bulk-magnet-footer">
        <span id="bulkImageCount">0 liens détectés</span>
      </div>
    </div>
    <div class="bulk-magnet-actions">
      <button type="button" class="btn btn-primary" id="bulkImageConfirm">Ajouter ces X liens</button>
      <button type="button" class="btn btn-outline" id="bulkImageCancel">Annuler</button>
    </div>
  </div>
</div>
```

Chaque entrée image a un champ magnet + un champ `label` (nom) :

```html
<div class="magnet-entry image-magnet-entry">
  <input type="text" name="image_magnet_link[]" placeholder="magnet:?xt=urn:btih:..." class="form-control flex-3" />
  <input type="text" name="image_label[]" placeholder="Nom de l'image (ex: Carte 2024)" class="form-control flex-2" />
  <button type="button" class="btn btn-outline remove-image-btn">✕</button>
</div>
```

#### Backend : téléchargement et cache

**Nouveau module `src/image_cache.py`** :

```python
# src/image_cache.py
import hashlib
import os
import threading
import time
from pathlib import Path

CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "instance" / "image_cache"
CACHE_TTL = 86400 * 30  # 30 jours

def _cache_path(magnet_link: str) -> Path:
    h = hashlib.sha256(magnet_link.encode()).hexdigest()[:16]
    return CACHE_DIR / h

def get_cached_image(magnet_link: str) -> bytes | None:
    """Retourne l'image depuis le cache si elle existe et n'a pas expiré."""
    p = _cache_path(magnet_link)
    if p.exists():
        mtime = os.path.getmtime(p)
        if time.time() - mtime < CACHE_TTL:
            return p.read_bytes()
    return None

def cache_image(magnet_link: str, data: bytes, ext: str = ".png") -> str:
    """Stocke l'image en cache. Retourne le chemin relatif pour src."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _cache_path(magnet_link)
    p.write_bytes(data)
    return f"/static/cache/img/{p.name}{ext}"

def download_image_from_magnet(magnet_link: str, timeout: int = 60) -> tuple[bytes | None, str | None]:
    """
    Télécharge la première image trouvée dans le torrent via libtorrent.
    Retourne (data_bytes, extension) ou (None, None) si échec.
    """
    import libtorrent as lt
    
    session = lt.session({"listen_interfaces": "0.0.0.0:6881"})
    session.start_dht()
    
    try:
        handle = session.add_magnet_torrent({"url": magnet_link, "paused": False})
        start = time.time()
        
        while not handle.has_metadata():
            if time.time() - start > timeout:
                return None, None
            time.sleep(0.5)
        
        fi = handle.get_file_info()
        # Trouver le premier fichier image
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
        image_files = [
            (idx, f) for idx, f in enumerate(fi)
            if any(f.name.lower().endswith(ext) for ext in image_extensions)
        ]
        
        if not image_files:
            return None, None
        
        idx, target = image_files[0]
        ext = Path(target.name).suffix.lower()
        
        # Priorité max pour ce fichier uniquement
        priorities = [0] * len(fi)
        priorities[idx] = 4
        handle.set_file_priority(priorities)
        
        # Attendre le téléchargement
        start = time.time()
        while True:
            if time.time() - start > timeout:
                return None, None
            if handle.file_status(idx).completed:
                break
            time.sleep(0.5)
        
        # Lire depuis le cache disque de libtorrent
        save_path = handle.status().save_path
        file_path = Path(save_path) / target.name
        if file_path.exists():
            return file_path.read_bytes(), ext
        
        return None, None
    finally:
        session.pause()
```

**Modification de `/api/upload/item`** dans `src/user_routes.py` :

Après la création de l'item, ajouter une étape qui traite les `image_magnet_links[]` :

```python
# Dans create_upload_item(), après db.session.flush() de l'item :

image_magnets = data.get("image_magnets", [])  # [{magnet_link, label}]
if image_magnets:
    from src.image_cache import get_cached_image, cache_image, download_image_from_magnet
    
    def _process_image_magnets(item_id, image_magnets):
        """Tâche asynchrone : télécharge les images et crée les ItemGallery."""
        from app import db as app_db
        for img in image_magnets:
            magnet = img.get("magnet_link", "").strip()
            label = img.get("label", "").strip()
            if not magnet:
                continue
            
            # Vérifier le cache
            data = get_cached_image(magnet)
            ext = ".png"
            if data is None:
                # Télécharger depuis le torrent
                data, ext = download_image_from_magnet(magnet)
                if data is None:
                    continue  # Échec, on skip
                ext = ext or ".png"
            
            src = cache_image(magnet, data, ext)
            
            gallery = ItemGallery(
                item_id=item_id,
                media_type="image",
                src=src,
                label=label or "Image",
                data_json={
                    "magnet_link": magnet,
                    "original_filename": f"image{ext}",
                },
            )
            with app_db.session.begin():
                app_db.session.add(gallery)
    
    # Lancer en arrière-plan pour ne pas bloquer la réponse HTTP
    thread = threading.Thread(
        target=_process_image_magnets,
        args=(item.id, image_magnets),
        daemon=True,
    )
    thread.start()
```

Le téléchargement se fait **en arrière-plan** (thread séparé) pour ne pas bloquer la réponse à l'utilisateur. Les images apparaîtront sur la fiche item dès que le téléchargement est terminé (rafraîchissement de page).

#### Template item_detail : afficher les magnets des images

Sur la page item (`templates/item_detail.html`), chaque image de la galerie affiche son lien Magnet d'origine :

```html
{% for img in image_gallery %}
  <div class="gallery-item">
    <img src="{{ img.src }}" alt="{{ img.label }}" />
    <span class="gallery-label">{{ img.label }}</span>
    {% if img.magnet_link %}
      <details class="magnet-source">
        <summary>Lien Magnet source</summary>
        <code>{{ img.magnet_link[:80] }}{% if img.magnet_link|length > 80 %}...{% endif %}</code>
      </details>
    {% endif %}
  </div>
{% endfor %}
```

Il faut adapter `get_image_gallery()` dans `src/item_routes.py` pour inclure le magnet :

```python
def get_image_gallery(item):
    result = []
    for g in item.gallery_items:
        if g.media_type != "image":
            continue
        entry = {
            "src": g.src,
            "label": g.label,
        }
        if g.data_json and isinstance(g.data_json, dict):
            entry["magnet_link"] = g.data_json.get("magnet_link", "")
        result.append(entry)
    return result
```

#### JS : logique des entrées image

Dans `upload.js`, même principe que les magnets de données mais sans les pills de zoom :

- `#addImageMagnetBtn` → ajoute une entrée avec magnet + label
- `#bulkImageMagnetBtn` → toggle la zone bulk
- `#bulkImageConfirm` → crée les entrées à partir des lignes du textarea
- À la soumission : collecter `image_magnet_link[]` + `image_label[]` → envoyer dans `itemPayload.image_magnets`

#### CSS additionnel

```css
.image-magnet-entry {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.image-magnet-entry .form-control.flex-3 {
  flex: 3;
}

.image-magnet-entry .form-control.flex-2 {
  flex: 2;
}
```

#### Dépendances

Ajouter à `requirements.txt` :
```
libtorrent>=2.0.9
```

---

### Volet 5 — Animation de chargement (spinner)

Après avoir cliqué sur "Publier", un overlay avec un spinner rond apparaît au-dessus de tout le formulaire pour indiquer que le traitement est en cours. Le formulaire devient inerte (plus de clics possibles).

#### Template

Juste avant la fermeture `</form>`, ajouter l'overlay :

```html
<div id="uploadSpinnerOverlay" class="spinner-overlay hidden-section">
  <div class="spinner-card">
    <div class="spinner-circle"></div>
    <p class="spinner-text" id="spinnerText">Téléversement en cours...</p>
    <p class="spinner-subtext" id="spinnerSubtext"></p>
    <!-- Si des images sont en cours de téléchargement -->
    <div id="spinnerImagesPending" class="hidden-section">
      <p class="spinner-images-note">⏳ Images en cours de téléchargement depuis Magnet...</p>
    </div>
  </div>
</div>
```

#### CSS

```css
.spinner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.spinner-overlay.hidden-section {
  display: none !important;
}

.spinner-card {
  background: var(--white);
  border-radius: 12px;
  padding: 2.5rem 2rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  max-width: 340px;
}

.spinner-circle {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color);
  border-top-color: var(--forest);
  border-radius: 50%;
  margin: 0 auto 1.25rem;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner-text {
  font-size: 1rem;
  font-weight: 600;
  color: var(--charcoal);
  margin: 0 0 0.25rem;
}

.spinner-subtext {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0;
}

.spinner-images-note {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0.75rem 0 0;
  font-style: italic;
}
```

#### JS (dans `upload.js`)

Ajouter les états du spinner :

```javascript
const spinnerOverlay = document.getElementById('uploadSpinnerOverlay');
const spinnerText = document.getElementById('spinnerText');
const spinnerSubtext = document.getElementById('spinnerSubtext');
const spinnerImagesPending = document.getElementById('spinnerImagesPending');

function showSpinner(text, subtext, showImages) {
  spinnerText.textContent = text;
  spinnerSubtext.textContent = subtext || '';
  if (showImages) {
    spinnerImagesPending.classList.remove('hidden-section');
  } else {
    spinnerImagesPending.classList.add('hidden-section');
  }
  spinnerOverlay.classList.remove('hidden-section');
  // Empêcher le scroll
  document.body.style.overflow = 'hidden';
}

function hideSpinner() {
  spinnerOverlay.classList.add('hidden-section');
  document.body.style.overflow = '';
}
```

Séquence lors de la soumission :

```javascript
// Au début du submit :
showSpinner('Envoi des données...', 'Étape 1/2');

// Après réponse de /api/upload/file :
showSpinner('Création de l\'item...', 'Étape 2/2');

// Après réponse de /api/upload/item :
const hasImages = itemPayload.image_magnets && itemPayload.image_magnets.length > 0;
if (hasImages) {
  showSpinner('Publication réussie !', 'Téléchargement des images en arrière-plan...', true);
  // Laisser le spinner 2 secondes puis rediriger
  setTimeout(() => {
    window.location.href = '/catalogue/item/' + itemData.id;
  }, 2000);
} else {
  showSpinner('Publication réussie !', 'Redirection...');
  setTimeout(() => {
    window.location.href = '/catalogue/item/' + itemData.id;
  }, 1500);
}

// En cas d'erreur :
hideSpinner();
```

On supprime l'ancienne `#uploadProgress` (barre horizontale) au profit du spinner.

---

### Volet 6 — Mode brouillon

Permettre à l'utilisateur de sauvegarder un item non finalisé pour le reprendre plus tard.

#### Modèle (`models.py`)

Ajouter une colonne `status` sur `Item` :

```python
status: Mapped[str] = mapped_column(default="published")
# "published" | "draft"
```

#### Template upload : bouton "Brouillon"

Deux boutons de soumission au lieu d'un seul :

```html
<div class="form-actions upload-actions">
  <button type="submit" class="btn btn-primary" id="uploadBtn">
    Publier les données
  </button>
  <button type="button" class="btn btn-outline" id="draftBtn">
    Enregistrer comme brouillon
  </button>
  <span class="form-status" id="uploadStatus"></span>
</div>
```

#### JS : soumission brouillon

Le brouillon ignore la validation stricte (pas de magnet requis, pas de données CSV requises). Au clic sur "Brouillon" :

```javascript
draftBtn.addEventListener('click', async function() {
  // Validation minimale : juste le titre
  const title = document.getElementById('title').value.trim();
  if (!title) {
    uploadStatus.textContent = 'Le titre est requis même pour un brouillon';
    uploadStatus.className = 'form-status form-error';
    return;
  }

  showSpinner('Enregistrement du brouillon...', '');

  const payload = buildItemPayload(true); // isDraft = true
  payload.status = 'draft';

  try {
    const csrfToken = CsrfModule.getCsrfToken();
    const response = await fetch('/api/upload/item', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (response.ok) {
      hideSpinner();
      window.location.href = '/catalogue/item/' + data.id;
    } else {
      hideSpinner();
      uploadStatus.textContent = data.error || 'Erreur';
      uploadStatus.className = 'form-status form-error';
    }
  } catch (err) {
    hideSpinner();
    uploadStatus.textContent = 'Erreur réseau';
    uploadStatus.className = 'form-status form-error';
  }
});
```

Le payload envoyé au brouillon est **allégé** : pas d'appel à `/api/upload/file`, pas de chunk CSV. Uniquement les métadonnées.

#### Backend (`src/user_routes.py`)

Modifier `/api/upload/item` pour accepter le statut brouillon :

```python
status = data.get("status", "published").strip()
if status not in ("published", "draft"):
    status = "published"

# ...

item = Item(
    # ... champs existants ...
    status=status,
)
```

Si `status == "draft"` :
- Ne pas exiger de `magnet_link`
- Ne pas exiger de `chunk_id`
- Ne pas lancer le téléchargement d'images (le faire seulement au moment de la publication)

#### Page "Mes brouillons"

Nouvelle route et template pour lister les brouillons de l'utilisateur :

```python
# src/user_routes.py
@bp.route("/brouillons")
@login_required
def brouillons_page():
    current_user = get_current_user()
    drafts = Item.query.filter_by(
        owner_user_id=current_user.id,
        status="draft",
    ).order_by(Item.created_at.desc()).all()
    return render_template(
        "users/brouillons.html",
        title="A.N.A.N.A.S. | Mes brouillons",
        drafts=drafts,
    )
```

Template `templates/users/brouillons.html` :

```html
<ul class="draft-list">
  {% for draft in drafts %}
  <li class="draft-item">
    <a href="/upload?edit={{ draft.id }}">{{ draft.title }}</a>
    <span>{{ draft.created_at.strftime('%d/%m/%Y') }}</span>
    <span class="badge">Brouillon</span>
    <a href="/upload?edit={{ draft.id }}" class="btn btn-sm">Modifier</a>
  </li>
  {% endfor %}
</ul>
<p class="draft-empty">Aucun brouillon.</p>
```

#### Reprendre un brouillon

Quand l'URL contient `?edit=<id>`, la page upload pré-remplit le formulaire avec les données du brouillon. À la soumission, on fait un PUT au lieu d'un POST, et le statut passe à `published`.

```python
# src/user_routes.py — nouvelle route
@bp.route("/api/upload/item/<int:item_id>", methods=["PUT"])
@login_required
def update_draft_item(item_id):
    # Vérifier que l'item appartient à l'utilisateur et est un brouillon
    # Mettre à jour les champs + passer status="published"
    # Lancer le téléchargement d'images si nécessaire
```

#### Statut visuel sur la page item

Si `item.status == "draft"`, une bannière en haut de la page :

```html
{% if item.status == "draft" %}
<div class="draft-banner">
  Ce contenu est un brouillon. <a href="/upload?edit={{ item.id }}">Reprendre l'édition</a>
</div>
{% endif %}
```

---

## Récapitulatif des 7 volets

| Volet | Description | Impact back |
|---|---|---|
| 0 | Tutoriel / visite guidée au premier affichage | Aucun — CSS + JS |
| 1 | Suppression granularité, déduction auto pack/individual | Aucun |
| 2 | Pills zoom cliquables au lieu de select | Aucun |
| 3 | Ajout en lot (textarea + zoom commun) | Aucun |
| 4 | Images via Magnet → téléchargement + cache serveur | Oui — `src/image_cache.py` |
| 5 | Spinner overlay après soumission | Aucun — CSS + JS |
| 6 | Mode brouillon (save as draft + reprise + page liste) | Oui — `models.py` + `user_routes.py` + `item_routes.py` |

## Fichiers impactés

| Fichier | Changements |
|---|---|
| `templates/users/upload.html` | Supprimer `#data_format_level`, `#packMagnetGroup`, `#individualMagnetGroup`. Nouveau bloc `#magnetSection` avec entrées dynamiques + zone bulk. Nouvelle section images (magnet + label + bulk). **Bouton "Brouillon"**, **overlay spinner**. |
| `static/js/upload.js` | ~50 lignes supprimées (toggle, format level). ~150 lignes ajoutées (init entrée unique, pills zoom, bulk données, bulk images, **spinner**, **soumission brouillon**). |
| `static/css/features/upload-page.css` | ~80 lignes ajoutées (`.zoom-pill`, `.magnet-entry`, `.bulk-magnet-group`, `.magnet-actions`, `.image-magnet-entry`, **`.upload-spinner`**, **`.spinner-overlay`**). |
| `src/user_routes.py` | Ajout traitement `image_magnets` dans `/api/upload/item` — lancement téléchargement asynchrone. **Support du champ `status=draft`** dans `/api/upload/item`. |
| `src/image_cache.py` | **Nouveau** — téléchargement libtorrent, cache disque. |
| `src/item_routes.py` | Modification `get_image_gallery()` — inclure `magnet_link` depuis `data_json`. |
| `templates/item_detail.html` | Affichage lien Magnet source `<details>` sous chaque image de la galerie. |
| `models.py` | Ajout colonne `status` sur `Item` (`published` / `draft`). |
| `requirements.txt` | Ajout `libtorrent>=2.0.9`. |

## Ordre d'implémentation

1. **CSS** — styles pills zoom, zone bulk, entrées image, spinner overlay
2. **Template upload** — nouveau markup section magnet + section images + bouton brouillon + overlay spinner
3. **JS upload** — nouvelle logique (init entrée unique, pills zoom, bulk, spinner, draft submit)
4. **`models.py`** — ajout colonne `status` sur `Item`
5. **`src/image_cache.py`** — module téléchargement + cache images
6. **`src/user_routes.py`** — traitement images magnet + support `status=draft`
7. **`src/item_routes.py`** — adapter `get_image_gallery()` pour exposer `magnet_link`
8. **Template item_detail** — afficher lien Magnet source sous les images
9. **`requirements.txt`** — ajouter `libtorrent`
10. **Tests** — vérifier : 1 magnet → pack, 2+ → individual, bulk, spinner, draft, image magnet
