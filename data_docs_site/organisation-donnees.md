# Organisation des données

## Structure hiérarchique

Les données sont organisées selon une hiérarchie à plusieurs niveaux :

```
Organisation
  └── Item (donnée, carte ou application)
        ├── Tags (mots-clés descriptifs)
        ├── Galerie (images, cartes interactives, CSV, dashboards)
        ├── Visualisation Links (liens externes, widgets embarqués)
        ├── Ratings (notes 1-5)
        ├── Commentaires (hiérarchiques avec réponses)
        ├── DataChunks (sous-éléments, pour les items individuels)
        ├── UserUploads (historique des uploads)
        └── SimpleFileItem (fichier simple mis en avant sur l'accueil)
```

---

## Le modèle Item

Le modèle Item (`Item`) possède les attributs suivants liés à la distribution :

| Champ | Description |
|-------|-------------|
| `type` | Catégorie : `geodonnee`, `carte`, `application` |
| `format_type` | Format technique (ex: shapefile, GeoJSON, GPKG) |
| `data_format_level` | Niveau : `simple`, `pack` ou `individual` |
| `magnet_link` | Lien magnet principal pour télécharger les données |
| `pdf_magnet_link` | Lien magnet optionnel pour la documentation PDF |
| `image_magnet_links` | Liste de magnets pour les images de la galerie |
| `license_type` | Licence associée (ex: Open Data Commons, CC-BY, etc.) |

---

## Fichiers simples (SimpleFileItem)

Les **fichiers simples** sont des items mis en avant sur la page d'accueil par les administrateurs. Le modèle `SimpleFileItem` permet de sélectionner et ordonner des items du catalogue pour les afficher dans une section dédiée.

| Champ | Description |
|-------|-------------|
| `item_id` | Référence vers l'Item à mettre en avant |
| `display_order` | Ordre d'affichage sur la page d'accueil |
| `is_active` | Active/Désactive l'affichage sans supprimer |

**API d'administration** :
- `GET /api/admin/simple-files` — Lister tous les fichiers simples
- `POST /api/admin/simple-files` — Ajouter un fichier simple (nécessite `item_id`)
- `PUT /api/admin/simple-files/<id>` — Modifier l'ordre ou l'état d'activation
- `DELETE /api/admin/simple-files/<id>` — Supprimer un fichier simple

**Paramètre global** : `home_show_simple_files` (activé par défaut) — contrôle l'affichage de la section "Fichiers Simples" sur la page d'accueil. Configurable depuis `/admin/settings`.

---

## Les organisations

Les **organisations** sont des entités collaboratives qui publient et gèrent des données sur la plateforme :

- Une organisation peut posséder plusieurs items (`Item.organization_id`)
- Chaque organisation a un **slug unique** utilisé dans l'URL (`/organizations/<slug>`)
- Les membres ont des **rôles** avec des permissions granulaires :

| Rôle | Permissions |
|------|-------------|
| Membre | Consultation uniquement |
| Modérateur | Retirer des membres, modérer le contenu |
| Éditeur | Gérer les éléments (CRUD) |
| Admin | Inviter/retirer des membres, éditer l'org, gérer les éléments, modérer |
| Propriétaire | Toutes les permissions, y compris gérer les rôles et supprimer l'org |

- Des **rôles personnalisés** avec permissions sur mesure peuvent être créés via `OrganizationRole`
- Les organisations peuvent être **publiques** (visibles dans le catalogue) ou **actives/inactives**

---

## Types de catalogue

Les items sont répartis en trois catalogues distincts :

1. **Données** (`/catalogue/donnees`) — Fichiers SIG, shapefiles, GeoJSON, CSV géoréférencés
2. **Cartes** (`/catalogue/cartes`) — Produits cartographiques, tuiles, fonds de carte
3. **Applications** (`/catalogue/applications`) — Services web, outils géospatiaux, dashboards

Chaque catalogue supporte le filtrage par :
- Statut de vérification (`verified`, `unofficial`, `rejected`)
- Organisation
- Niveau de format (`simple` / `pack` / `individual`)

---

## Formats supportés

| Type | Formats | Distribution |
|------|---------|--------------|
| Géodonnées | SIG, shapefiles, GeoJSON, CSV, GPKG | Magnet link obligatoire |
| Cartes | Produits cartographiques, tuiles, cartes interactives | Magnet link obligatoire |
| Applications | Services web, outils géospatiaux | Magnet link obligatoire |

---

## Intégrité et sécurité

### Aucune donnée stockée sur le serveur

La plateforme A.N.A.N.A.S. **n'héberge aucun fichier de données**. Seuls les métadonnées descriptives (titre, description, tags, organisation) et les liens magnet sont stockés dans la base de données PostgreSQL. Les données réelles circulent exclusivement sur le réseau BitTorrent.

L'interface d'upload permet uniquement de créer des **prévisualisations** (CSV d'aperçu, galerie d'images téléchargées depuis le P2P via qBittorrent) et des **liens de visualisation** externes. Ces données annexes sont strictement décoratives et ne remplacent en aucun cas le magnet link obligatoire.

### Vérification des magnet links (obligatoire)

Tous les magnet links sont validés par `validate_magnet_link()` avant d'être stockés. Un item sans magnet link valide ne peut pas être publié. Le format attendu est :

```
magnet:?xt=urn:btih:<INFO_HASH>&dn=<NAME>&tr=<TRACKER_URL>
```

### Statut de vérification

Les items peuvent avoir les statuts suivants :
- `verified` — Vérifié par un administrateur (données officielles)
- `unofficial` — Non vérifié (données publiées par un utilisateur sans validation)
- `rejected` — Rejeté par la modération

La vérification est effectuée par les administrateurs depuis le panneau d'administration.

---

## Score IMOD (Indice de qualité)

Chaque item dispose d'un **score IMOD** qui évalue sa qualité de manière composite. Le score est calculé selon trois dimensions :

| Dimension | Poids | Critères évalués |
|-----------|-------|------------------|
| **Métadonnées** | 45% | Description (0-2pts), tags (0-2pts), licence (0-2pts), auteur (0-1pt), organisation (0-1pt), documentation PDF (0-2pts) |
| **Technique** | 36% | Format type (0-2pts), magnet valide (0-2pts), niveau de format (0-3pts) |
| **Richesse** | 19% | Galerie (0-3pts), liens visualisation (0-2pts), ratings (0-2pts), commentaires (0-2pts), images magnet (0-1pt) |

**Bonus** : +20 points si l'item est vérifié par un administrateur.

**Seuils d'interprétation** :
- **Élevé** (≥70) — Item de qualité optimale
- **Moyen** (≥40) — Item avec des métadonnées complètes
- **Faible** (<40) — Item nécessitant des améliorations