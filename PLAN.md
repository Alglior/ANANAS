# Plan de Développement — A.N.A.N.A.S. v2

> **Statut :** En attente d'implémentation  
> **Date :** 2026-05-14

---

## Table des matières

1. [Refonte index.html — Sections Cartes/Applications](#1-refonte-indexhtml--sections-cartesapplications)
2. [Documentation du site](#2-documentation-du-site)
3. [Header — Boutons supplémentaires](#3-header--boutons-supplémentaires)
4. [Modèle Item — Différenciation Pack / Données individuelles](#4-modèle-item--différenciation-pack--données-individuelles)
5. [Interface Utilisateur (utilisateur lambda)](#5-interface-utilisateur-utilisateur-lambda)
6. [Interface Admin](#6-interface-admin)
7. [Création automatique du compte admin au premier lancement](#7-création-automatique-du-compte-admin-au-premier-lancement)
8. [Correction du système de rating](#8-correction-du-système-de-rating)
9. [Zone de commentaire — Suppression du champ author readonly](#9-zone-de-commentaire--suppression-du-champ-author-readonly)
10. [Barre de recherche avec tags et filtres](#10-barre-de-recherche-avec-tags-et-filtres)
11. [Recherche avancée avec bouton dédié](#11-recherche-avancée-avec-bouton-dédié)
12. [Précision géographique dans les packs](#12-précision-géographique-dans-les-packs)
13. [Page de redirection si pas de visualisation](#13-page-de-redirection-si-pas-de-visualisation)

---

## 1. Refonte index.html — Sections Cartes / Applications

**Fichier :** `templates/index.html`

### Objectif
Séparer les cartes et applications en sections distinctes sur la page d'accueil, parallèlement à la section Packs GeoPackage et Données Individuelles existante.

### Tâches

### [ ] 1.1 — Ajouter une section "Cartes" (`#cartes`)
- Créer une nouvelle section `<section class="maps-section" id="cartes">` après la section `donnees-individuelles`
- Inclure :
  - Un header avec titre et sous-texte descriptif
  - Une grille de cartes (3-4 exemples) montrant les types de cartes disponibles
  - Chaque carte : icône SVG, titre court, description, badge format/type
  - Un bouton CTA vers `/catalogue/cartes`

### [ ] 1.2 — Ajouter une section "Applications" (`#applications`)
- Créer `<section class="apps-section" id="applications">` après la section `cartes`
- Inclure :
  - Un header avec titre et sous-texte descriptif
  - Une grille de cartes (3-4 exemples) d'applications disponibles
  - Chaque carte : icône, titre, description, badge type (dashboard, viewer, etc.)
  - Un bouton CTA vers `/catalogue/applications`

### [ ] 1.3 — Ajouter le CSS associé
- Fichier : `static/css/features/sections/maps.css` (si nouvelle section) ou ajouter à `features/sections/individual-data.css`
- Créer : `.maps-section`, `.apps-section` et leurs sous-classes en cohérence avec les sections existantes (`gp-section`, `di-section`)

### [ ] 1.4 — Inclure le CSS dans `static/css/style.css`
- Ajouter l'import des nouveaux styles de section (ordre logique après individual-data)

### [ ] 1.5 — Adapter la navigation et les CTA
- S'assurer que les liens CTA pointent vers les bons catalogues (`/catalogue/cartes`, `/catalogue/applications`)
- Vérifier que l'ancre `#cartes` et `#applications` fonctionne dans la navbar

---

## 2. Documentation du site

**Fichiers concernés :** `ARCHITECTURE.md`, `README.md` (nouveau ou mis à jour)

### Tâches

### [ ] 2.1 — Créer un dossier `/docs/` dédié
- `mkdir docs/`
- Fichier : `docs/SITE_DOCUMENTATION.md` — documentation utilisateur complète

### [ ] 2.2 — Rédiger la documentation utilisateur (`docs/SITE_DOCUMENTATION.md`)
Contenu à inclure :
- **Introduction** : Qu'est-ce qu'A.N.A.N.A.S., objectif du portail
- **Accéder au site** : URL, prérequis (navigateur, client BitTorrent)
- **Parcourir le catalogue** : Comment naviguer entre géodonnées, cartes, applications
- **Télécharger des données** : Étapes détaillées avec lien magnet
- **Interagir** : Créer un compte, noter, commenter, signaler
- **Glossaire** : GeoPackage, BitTorrent, magnet link, tag, zoom géographique
- **FAQ** : Questions fréquentes

### [ ] 2.3 — Ajouter une page "Documentation" dans le site (accessible depuis la navbar)
- Route : `GET /docs` dans un nouveau blueprint ou dans `app.py`
- Template : `templates/docs.html` (étendant `base.html`)
- Contenu dynamique chargé depuis `docs/SITE_DOCUMENTATION.md`

### [ ] 2.4 — Ajouter le lien "Docs" dans la navbar du header
- Modifier `templates/partials/header.html` pour ajouter un lien vers `/docs` dans le `<nav>`
- Le placer après "Catalogue" et avant "Contact"

---

## 3. Header — Boutons supplémentaires

**Fichier :** `templates/partials/header.html`, CSS associé

### Tâches

### [ ] 3.1 — Identifier les boutons à ajouter
- **Bouton "Aide"** : lien vers `/docs` ou un modal d'aide contextuel
- **Bouton "Mon profil"** (visible seulement si `current_user`) : lien vers une page de profil futur (`/profil`)

### [ ] 3.2 — Ajouter le bouton "Aide" dans la zone auth-actions
- Placer entre le nom d'utilisateur et le bouton déconnexion
- Icône `?` SVG, classe `.btn-help`

### [ ] 3.3 — Ajouter le bouton "Mon profil" (conditionnel)
- Visible uniquement pour les utilisateurs connectés
- Classe `.btn-profile`, lien vers `/profil`

### [ ] 3.4 — Style des nouveaux boutons dans `static/css/header.css`
- Cohérence avec `.btn-outline` existant
- Hover states, icon spacing

---

## 4. Modèle Item — Différenciation Pack / Données individuelles

**Fichiers :** `models.py`, migrations Alembic, templates (`catalogue.html`, `item_detail.html`)

### Tâches

### [ ] 4.1 — Ajouter le champ `data_format_level` dans le modèle `Item`
Dans `models.py`, ajouter après `verification_status` :
```python
data_format_level: Mapped[str] = mapped_column(
    default="individual"  # "pack" ou "individual"
)
```
- `"pack"` : données regroupées en un seul fichier GeoPackage (ex: pack complet d'une région)
- `"individual"` : données individuelles avec plusieurs niveaux de zoom téléchargeables séparément

### [ ] 4.2 — Créer la migration Alembic
- Lancer `flask db migrate -m "add data_format_level to items"`
- Vérifier le fichier de migration généré dans `alembic/versions/`
- Tester avec `flask db upgrade`

### [ ] 4.3 — Ajouter le champ dans `to_dict()` du modèle Item
```python
"data_format_level": self.data_format_level,
"download_levels": [...],  # optionnel: liste de niveaux de zoom pour les données individuelles
```

### [ ] 4.4 — Mettre à jour les routes d'upload / création d'items
- Modifier `src/upload_routes.py` pour accepter le champ `data_format_level`
- Ajouter la logique selon laquelle un pack a un seul magnet_link, tandis qu'un item individuel peut en avoir plusieurs

### [ ] 4.5 — Adapter l'affichage dans `item_detail.html`
- Afficher un badge différencié selon le type :
  - Pack → badge "Pack complet — fichier unique"
  - Individuel → badge avec liste des niveaux de zoom disponibles (si applicable)

---

## 5. Interface Utilisateur (utilisateur lambda)

### Tâches

### [ ] 5.1 — Créer une page de profil utilisateur (`/profil`)
- Template : `templates/profil.html`
- Contenu : informations personnelles, mot de passe, préférences d'affichage
- Formulaire modifiable pour : prénom, nom, email
- Bouton "Modifier le mot de passe" (formulaire séparé)

### [ ] 5.2 — Créer la route correspondante
- Dans `src/auth_routes.py` ou un nouveau blueprint `user_routes.py`
- `GET /profil` — affichage des données utilisateur
- `PUT /api/users/profile` — mise à jour du profil (JSON API)
- `POST /api/users/change-password` — changement de mot de passe

### [ ] 5.3 — Afficher le nombre de contributions de l'utilisateur
- Dans la page profil :
  - Nombre d'items notés
  - Nombre de commentaires publiés
  - Organisation(s) membres

### [ ] 5.4 — Page "Mon activité" (`/activite`)
- Template : `templates/activite.html`
- Historique des actions : notes, commentaires, téléchargements récents
- Route : `GET /activite` (requiert `@login_required`)

---

## 6. Interface Admin

**Fichiers actuels :** `src/admin_routes.py`, `templates/admin/users.html`, `templates/admin/reports.html`

### Tâches

### [ ] 6.1 — Créer un dashboard admin global (`/admin`)
- Template : `templates/admin/dashboard.html`
- Statistiques générales : nombre d'utilisateurs, items, organisations, rapports en attente
- Navigation vers les sous-pages existantes (`/admin/users`, `/admin/reports`)

### [ ] 6.2 — Créer la route du dashboard
- Dans `src/admin_routes.py` :
```python
@bp.route("/admin")
@admin_required
def admin_dashboard():
    # Récupérer stats et rendre template
```

### [ ] 6.3 — Ajouter une page de gestion des items (`/admin/items`)
- Template : `templates/admin/items.html`
- Tableau listant tous les items avec filtres (statut de vérification, type, organisation)
- Actions en ligne : vérifier, rejeter, supprimer

### [ ] 6.4 — Ajouter la route de gestion des items
- Dans `src/admin_routes.py` :
```python
@bp.route("/admin/items")
@admin_required
def admin_items(): ...

@bp.route("/api/admin/items/<int:item_id>/action", methods=["POST"])
@admin_required
def admin_item_action(): ...  # vérification, suppression
```

### [ ] 6.5 — Ajouter une page de gestion des organisations (`/admin/organizations`)
- Template : `templates/admin/organizations.html`
- Liste des organisations avec statut actif/inactif
- Actions : suspendre, supprimer, modifier

### [ ] 6.6 — Créer un guard `@admin_required` dans `src/shared.py`
```python
from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from src.shared import get_current_user
        current_user = get_current_user()
        if not current_user or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated
```

### [ ] 6.7 — Ajouter un lien "Admin" dans le header (visible uniquement pour les admins)
- Modifier `templates/partials/header.html` :
```html
{% if current_user and current_user.is_admin %}
<a href="/admin">Admin</a>
{% endif %}
```

---

## 7. Création automatique du compte admin au premier lancement

### Tâches

### [ ] 7.1 — Identifier le point d'entrée principal
- Fichier : `app.py` — la fonction `create_app()` est le point d'entrée idéal
- Ou : script de migration initiale dans `alembic/`

### [ ] 7.2 — Créer un signal / hook post-migration pour le compte admin
Option A (dans `app.py` après initialisation DB) :
```python
def ensure_admin_exists():
    from models import User
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        # Créer l'admin à partir de vars d'environnement ou par défaut
        admin = User(
            prenom="Admin",
            nom="Système",
            email=os.environ.get("ADMIN_EMAIL", "admin@ananas.org"),
            password_hash=generate_password_hash(os.environ.get("ADMIN_PASSWORD", "changeme")),
            is_active=True,
            banned=False,
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
```

### [ ] 7.3 — Intégrer dans le cycle de démarrage
- Appeler `ensure_admin_exists()` dans `create_app()` après `db.create_all()` ou après les migrations Alembic
- Ajouter un log message : `"Admin account created/verified: admin@ananas.org"`

### [ ] 7.4 — Variables d'environnement pour l'admin par défaut
Ajouter à `.env.example` :
```env
ADMIN_EMAIL=admin@ananas.org
ADMIN_PASSWORD=changeme
```

### [ ] 7.5 — Avertissement de sécurité dans le log
- Si les creds sont aux valeurs par défaut (`changeme`), afficher un warning
- Vérifier que `ADMIN_PASSWORD` est modifié en production via `.env`

---

## 8. Correction du système de rating

**Fichier problématique :** `src/interactions.py` — la fonction `rate_item()`
**Fichiers liés :** `models.py:78-80`, `templates/item_detail.html:74-85`

### Tâches

### [ ] 8.1 — Identifier le bug : `format_type` écrasé au lieu de `_rating_avg`
Dans `interactions.py:31` :
```python
# Actuel (CORROMPU) :
item.format_type = getattr(item, "_rating_avg", None) or 0

# Devient :
# Ne PAS modifier format_type du tout
```

### [ ] 8.2 — Corriger la logique de calcul du rating moyen
Dans `models.py:_get_rating_avg()` (lignes 77-80) :
```python
def _get_rating_avg(self):
    if not self.ratings:
        return None  # Retourner None au lieu d'une valeur par défaut arbitraire (3.8)
    return sum(r.rating for r in self.ratings) / len(self.ratings)
```

### [ ] 8.3 — Corriger la route `rate_item()` dans `interactions.py`
Refactorisation complète de la fonction :
```python
@bp.route("/catalogue/item/<int:item_id>/rate", methods=["POST"])
def rate_item(item_id):
    from models import Item, Rating

    item = Item.query.get_or_404(item_id)
    rating_value = request.form.get("rating")

    if not rating_value or not rating_value.isdigit():
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    rating = int(rating_value)

    # Un utilisateur ne peut qu'une seule note par item
    existing = Rating.query.filter_by(
        item_id=item_id, user_id=get_current_user().id
    ).first()

    if existing:
        existing.rating = rating
    else:
        new_rating = Rating(item_id=item_id, user_id=get_current_user().id, rating=rating)
        db.session.add(new_rating)

    db.session.commit()
    return redirect(url_for("items.item_detail_view", item_id=item_id))
```

### [ ] 8.4 — Mettre à jour `to_dict()` pour un calcul dynamique du rating
Dans `models.py:73` :
```python
"rating": self._get_rating_avg() or 0,  # 0 au lieu de 3.8 par défaut
```

### [ ] 8.5 — Mettre à jour le template `item_detail.html` pour afficher correctement
- Si pas de rating : afficher "Pas encore noté" plutôt qu'un faux score
- Adapter les étoiles : si `rating == 0`, commencer avec des étoiles vides

---

## 9. Zone de commentaire — Suppression du champ author readonly

**Fichier :** `templates/item_detail.html` ligne 232

### Tâches

### [ ] 9.1 — Retirer l'input readonly `author` dans le formulaire de commentaire
Supprimer ces lignes dans `item_detail.html` :
```html
<input class="comment-input" type="text" name="author" value="{{ current_user.prenom }} {{ current_user.nom }}" readonly>
```

### [ ] 9.2 — Passer le nom de l'auteur via hidden ou session côté serveur
Option A (recommandée) : utiliser `current_user` directement dans la route backend
- Dans `src/interactions.py:add_comment()` (ligne 43), extraire l'auteur depuis `get_current_user()`
- Ignorer le champ `author` du formulaire

### [ ] 9.3 — Adapter la route `add_comment()` dans `interactions.py`
```python
@bp.route("/catalogue/item/<int:item_id>/comment", methods=["POST"])
def add_comment(item_id):
    from models import Item, Comment

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)
    
    # L'auteur est l'utilisateur connecté (pas besoin de champ form)
    author_name = f"{current_user.prenom} {current_user.nom}" if current_user else "Anonyme"
    
    content = sanitize_html(request.form.get("text", ""))

    if not content:
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    comment = Comment(
        item_id=item_id,
        author_name=author_name,
        content=content,
    )
    db.session.add(comment)
    db.session.commit()

    return redirect(url_for("items.item_detail_view", item_id=item_id))
```

### [ ] 9.4 — Mettre à jour le CSS des commentaires si nécessaire
- Retirer tout style spécifique à `.comment-input` s'il n'est plus utilisé
- Vérifier l'alignement du formulaire dans `static/css/features/comments.css`

---

## 10. Barre de recherche avec tags et filtres

**Fichiers :** `templates/partials/header.html`, `src/catalogue_routes.py`, `static/js/main.js`

### Tâches

### [ ] 10.1 — Remplacer la barre de recherche simple par une recherche à tags
- Modifier le formulaire dans `header.html` :
  - Ajouter un champ texte avec auto-complétion pour les tags existants
  - Afficher les tags sélectionnés sous forme de "chips" (pilotes cliquables)
  - Le bouton de soumission devient une loupe intégrée

### [ ] 10.2 — Créer la structure de données des tags disponibles
- API endpoint : `GET /api/tags` → retourne la liste unique de tous les tags dans le catalogue
- Endpoint dans `src/catalogue_routes.py` :
```python
@bp.route("/api/tags")
def get_tags():
    from models import ItemTag, db
    tags = [t.tag for t in ItemTag.query.distinct().all()]
    return jsonify(tags)
```

### [ ] 10.3 — Ajouter les options de scope de recherche
Ajouter un `<select>` à côté du champ de recherche :
- **Options** : "Tout le catalogue", "Géodonnées", "Cartes", "Applications"
- Valeurs transmises via paramètre `scope=donnees|cartes|applications|all`
- Adapter `_do_catalogue()` dans `catalogue_routes.py` pour filtrer selon ce scope

### [ ] 10.4 — Filtrer si déjà dans un catalogue spécifique
- Si l'utilisateur est sur `/catalogue/cartes`, la recherche ne cherche que dans les cartes par défaut
- Ajouter une option "Étendre à tout le catalogue" avec un toggle/checkbox

### [ ] 10.5 — Implémenter l'auto-complétion des tags en JS
- Dans `static/js/main.js` : écouter l'événement `input` sur le champ de recherche
- Envoyer une requête fetch vers `/api/tags?q=...`
- Afficher un dropdown avec les suggestions
- Au clic sur un tag, l'ajouter comme chip dans la zone de recherche

### [ ] 10.6 — Mettre à jour `_do_catalogue()` pour supporter la recherche par tags
```python
search_tags = request.args.getlist("tags")  # tableau de strings
if search_tags:
    query = query.filter(Item.tags.any(ItemTag.tag.in_(search_tags)))
```

---

## 11. Recherche avancée avec bouton dédié

**Fichiers :** `templates/partials/header.html`, `templates/search_advanced.html`, nouveaux endpoints

### Tâches

### [ ] 11.1 — Ajouter un bouton "Recherche avancée" à côté de la barre de recherche
- Modifier `header.html` : ajouter `<button class="btn-search-advanced" type="button">Advanced Search</button>`
- Icône d'engrenage ou texte "Avancé"

### [ ] 11.2 — Créer la page de recherche avancée (`/search/advanced`)
- Template : `templates/search_advanced.html`
- Inclure les champs de filtre suivants :
  - **Texte libre** (champ principal)
  - **Tags** (sélection multiple avec auto-complétion)
  - **Auteur** (champ texte)
  - **Titre** (champ texte, recherche partiellette)
  - **Organisation** (select dropdown)
  - **Format** (select : GPKG, SHP, GeoJSON, etc.)
  - **Taille min / max** (champs numériques en MB)
  - **Statut de vérification** (checkboxes)

### [ ] 11.3 — Ajouter la précision géographique avec carte Leaflet
- Inclure Leaflet via CDN dans le template (`<script src="leaflet...">`)
- Ajouter un div `#map` pour la carte interactive
- Sur la carte, superposer les items/packs comme marqueurs ou couches polygonales (geojson)
- L'utilisateur peut :
  - Cliquer/carrer une zone sur la carte → filtrer les données géographiquement
  - Cocher des catégories dans une sidebar (régions, dept, communes, IRIS)
  - OU utiliser une liste simple à la place de la carte

### [ ] 11.4 — Créer les endpoints API pour la recherche avancée
- `GET /api/search/advanced` : retourne les résultats basés sur tous les filtres combinés
- `GET /api/search/geodata` : retourne les données géographiques en GeoJSON pour la carte Leaflet
- Supporter les paramètres multiples : `q`, `tags[]`, `author`, `title`, `org`, `format`, `min_size`, `max_size`, `bbox` (pour la carte)

### [ ] 11.5 — Garder ou non les tags sélectionnés lors d'une recherche avancée
- Ajouter un checkbox "Conserver les tags de la recherche précédente"
- Si coché : fusionner avec les nouveaux tags
- Si décoché : ignorer les anciens tags

### [ ] 11.6 — Rediriger vers la page catalogue standard après recherche avancée
- Après soumission du formulaire avancé, rediriger vers `/catalogue?type=...&tags[]=...` pour garder le résultat dans le flux normal
- Ou afficher directement les résultats dans une grille style catalogue

---

## 12. Précision géographique dans les packs

**Fichiers :** `models.py`, templates, routes, données de seed

### Tâches

### [ ] 12.1 — Ajouter un champ `geographic_precision` au modèle Item
```python
geographic_precision: Mapped[str | None] = mapped_column(default=None)
# Valeurs : 'pays', 'region', 'departement', 'commune', 'iris', 'autre'
```

### [ ] 12.2 — Ajouter un champ `geo_coordinates` (JSON) au modèle Item
```python
geo_coordinates: Mapped[dict | None] = mapped_column(JSON, default=None)
# Exemple : {"bbox": [-5.0, 36.0, 10.0, 45.0], "center": [2.0, 40.0]}
```

### [ ] 12.3 — Créer la migration Alembic pour les deux nouveaux champs
- `flask db migrate -m "add geographic_precision and geo_coordinates to items"`
- Mettre à jour toutes les données existantes avec des valeurs par défaut (`"autre"`, `None`)

### [ ] 12.4 — Afficher la précision géographique dans le template `item_detail.html`
Dans la section `.product-details` ou `.tech-grid` :
```html
<dt>Zone géographique</dt>
<dd>{{ item.geographic_precision }}{% if item.geo_coordinates %} ({% for coord in item.geo_coordinates.center %}{{ coord }}{% endfor %}){% endif %}</dd>
```

### [ ] 12.5 — Afficher la précision dans les cartes du catalogue (`catalogue.html`)
- Ajouter un petit badge sous chaque carte d'item : `📍 Commune, Dept`
- Utiliser le champ `geographic_precision` pour déterminer l'affichage

### [ ] 12.6 — Utiliser dans la recherche avancée (tâche 11)
- Le filtre de localisation sur la carte et dans la liste doit filtrer par `geographic_precision`
- Si `bbox` est passé dans la requête, filtrer les items dont `geo_coordinates.bbox` intersecte le bbox

### [ ] 12.7 — Ajouter une vue de démo avec des données fictives pour tester
- Dans `scripts/seed_data.py`, ajouter des exemples d'items avec différentes précisions géographiques
- Vérifier que l'affichage sur l'index.html et catalogue est correct

---

## 13. Page de redirection si pas de visualisation

**Fichiers :** `templates/gallery.html`, `src/item_routes.py`

### Tâches

### [ ] 13.1 — Créer une page dédiée "Pas de visualisation disponible"
- Template : `templates/no_visualization.html`
- Contenu :
  - Message clair : *"Aucune visualisation n'a été mise à disposition pour cette donnée par l'individu ou l'organisation qui l'a publiée."*
  - Bouton : "Télécharger les données directement" (lien magnet)
  - Bouton : "Retour au catalogue"
  - Optionnel : bouton "Signaler / Demander une visualisation"

### [ ] 13.2 — Créer une route pour la page d'accueil de visualisation (`/catalogue/item/<id>/gallery`)
Dans `src/item_routes.py` :
```python
@bp.route("/catalogue/item/<int:item_id>/gallery")
def item_gallery_view(item_id):
    from models import Item

    item = Item.query.get_or_404(item_id)

    # Vérifier s'il y a des éléments de galerie (images, CSV, dashboards, maps interactives)
    has_visualization = any(
        g.media_type in ("image", "csv", "dashboard", "interactive_map")
        for g in item.gallery_items
    )

    if not has_visualization:
        from flask import render_template
        return render_template(
            "no_visualization.html",
            title=f"Visualisation — {item.title}",
            meta_description="Aucune visualisation disponible pour cet item",
            item=item.to_dict(),
        ), 404

    return render_template(
        "gallery.html",
        title=f"Galerie — {item.title}",
        meta_description="Galerie de " + item.title,
        item=item.to_dict(),
    )
```

### [ ] 13.3 — Mettre à jour les onglets dans `item_detail.html`
- Si pas de visualisation : désactiver le tab "Visualisation" (classe `.tab-btn.disabled`)
- Ajouter un `title` ou tooltip sur l'onglet désactivé : "Aucune visualisation disponible"
- Optionnel : ajouter une icône d'avertissement sur l'onglet

---

## Résumé des dépendances entre tâches

```
Tâche 7 (Admin auto) → Tâche 6 (Interface Admin) : L'interface admin nécessite un compte admin
Tâche 4 (Model Item)  → Tâche 12 (Geo precision) : Les champs géographiques nécessitent le model mis à jour
Tâche 8 (Rating fix)  → Indépendant, mais prioritaire (bug)
Tâche 9 (Comment bug) → Indépendant, mais prioritaire (bug UX)
Tâche 10 (Search tags) → Tâche 11 (Advanced search) : La recherche avancée utilise la base de tags
Tâche 4 (Model Item)  → Tâche 13 (No visualization) : Le modèle doit supporter les données gallery
```

## Ordre recommandé d'implémentation

| Priorité | Tâches | Raison |
|----------|--------|--------|
| **P0** | 8, 9 | Bugs critiques à corriger en premier |
| **P1** | 7 → 6.6, 6.1-6.5 | L'admin est nécessaire pour gérer les données |
| **P2** | 4.1-4.5 → 12.1-12.7 | Modifications du modèle avant l'affichage |
| **P3** | 10.1-10.6 → 11.1-11.6 | Recherche et recherche avancée (dépendent) |
| **P4** | 1.1-1.5, 2.1-2.4, 3.1-3.4, 5.1-5.4, 13.1-13.3 | Améliorations UI/UX indépendantes |
