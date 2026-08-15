# Guide d'utilisation

Bienvenue sur **A.N.A.N.A.S.** — *Atlas Numerique d'Archives de Noeuds et d'Acces Synchronises*, une plateforme de diffusion de données géospatiales via des protocoles décentralisés (P2P / BitTorrent / magnet links).

### Principes de la distribution P2P

Contrairement aux plateformes traditionnelles qui stockent les données sur un serveur central, A.N.A.N.A.S. distribue les données via un réseau **pair-à-pair (P2P)** utilisant le protocole **BitTorrent** :

- **Les données ne sont pas stockées sur le serveur** — Seuls les liens magnet (empreintes cryptographiques) sont hébergés
- **Chaque téléchargeur devient aussi un distributeur** — En téléchargeant, vous contribuez à la résilience du réseau
- **Pas de point de défaillance unique** — Le portail peut être hors ligne, les données restent accessibles entre pairs
- **Intégrité garantie** — Chaque fichier est vérifié par hachage SHA-1

> **Pour comprendre le fonctionnement détaillé du protocole**, consultez la page [P2P & BitTorrent](/docs/p2p-bittorrent).

---

## Fonctionnalités principales

### Catalogue de données
Trois catalogues distincts sont disponibles :

- **Données** (`/catalogue/donnees`) — Fichiers SIG, shapefiles, GeoJSON, CSV géoréférencés
- **Cartes** (`/catalogue/cartes`) — Produits cartographiques, tuiles, fonds de carte
- **Applications** (`/catalogue/applications`) — Services web, outils géospatiaux, widgets

Chaque catalogue est paginé (30 éléments par page) et propose des filtres par statut de vérification (vérifié / non officiel), organisation, et niveau de format (simple / pack / individuel). Accès JSON possible via `/catalogue/<type>/<page>/json`.

Les items sont présentés avec leur **format de distribution** (simple, pack ou individuel) et leur **lien magnet** direct, permettant de lancer le téléchargement P2P en un clic.

### Fichiers simples

La section **Fichiers Simples** de la page d'accueil (`/`) met en avant des items sélectionnés par les administrateurs. Ces fichiers sont des jeux de données au format **simple** (un seul fichier, une seule couche), prêts à l'emploi et disponibles en téléchargement direct via magnet.

- **Accès rapide** : un fichier unique, une seule couche, pas de configuration complexe
- **Prêt à l'emploi** : ouvrez directement dans QGIS, ArcGIS ou tout autre logiciel SIG
- **Sélection admin** : les fichiers simples sont curatés par les administrateurs de la plateforme

La visibilité de cette section peut être activée/désactivée depuis le panneau d'administration (`/admin/settings`).

### Navigation par page

| Page | URL | Description |
|------|-----|-------------|
| Accueil | `/` | Présentation, sites miroirs, éléments à la une, GeoPackages |
| Catalogue | `/catalogue/donnees` | Parcourir les données géospatiales |
| Détail d'un élément | `/catalogue/item/<id>` | Fiche complète avec galerie, notes, commentaires |
| Organisations | `/organizations` | Liste des organisations collaboratives |
| Contact | `/contact` | Formulaire de contact |
| Connexion | `/connexion` | Page de connexion |
| Inscription | `/inscription` | Création de compte |
| Documentation | `/docs` | Pages de documentation |

### Compte utilisateur

Une fois connecté, accédez à votre tableau de bord via `/compte` :

- **Informations** — Modifier votre prénom et nom
- **Sécurité** — Changer votre mot de passe (invalide les sessions existantes), activer la 2FA (authentification à deux facteurs)
- **Activité** — Historique de vos notes, commentaires, publications
- **Organisations** — Vos organisations et rôles

### Publication de données

1. Rendez-vous sur `/upload`
2. Remplissez les métadonnées (titre, description, type, format, licence)
3. **Choisissez le niveau de format** :
   - **Simple** : un seul fichier, une seule couche (ex: un CSV, un GeoJSON)
   - **Pack** : un seul fichier GeoPackage (.gpkg) contenant plusieurs couches
   - **Individuel** : plusieurs fichiers distincts
4. **Ajoutez un lien magnet** (obligatoire — les données ne sont pas hébergées sur le serveur)
5. Ajoutez des images via magnet links (optionnel — pour la galerie)
6. Ajoutez un lien magnet pour la documentation PDF (optionnel — améliore le score IMOD)
7. Ajoutez un lien de visualisation externe (optionnel — WMS, WFS, dashboard)
8. Ajoutez des tags et choisissez une organisation/licence
9. Publiez ou sauvegardez comme brouillon

**Fonctionnalités avancées de l'upload** :
- **Import JSON en masse** : déposez un ou plusieurs fichiers JSON pour créer plusieurs items d'un coup
- **Script Python** : un script de publication en masse est inclus dans l'interface
- **Score IMOD** : aperçu en temps réel de la qualité de vos métadonnées (score /100)
- **Tutorial interactif** : guide pas-à-pas pour les nouveaux utilisateurs
- **Brouillons** : sauvegardez votre travail et reprenez-le plus tard
- **Corbeille** : les éléments supprimés restent récupérables pendant 7 jours

### Organisations

Les organisations permettent de collaborer autour de jeux de données, structurant la publication et la gestion des données géospatiales :

- **Créer** une organisation avec un slug unique
- **Inviter** des membres par email
- **Gérer les rôles** : membre, modérateur, éditeur, admin, propriétaire
- **Rôles personnalisés** avec permissions granulaires (inviter, supprimer des membres, éditer, gérer les éléments, modérer, gérer les rôles, supprimer l'organisation)
- **Publier sous une organisation** : lors de la publication d'un item, associez-le à votre organisation pour crédibiliser la source et permettre une gestion collective
- **Page publique** : chaque organisation a sa propre page (`/organizations/<slug>`) listant tous ses items publiés

> **Pour plus de détails sur le modèle d'organisation et les permissions**, consultez la page [Organisation des données](/docs/organisation-donnees).

### Interactions

- **Notation** — Notez les éléments de 1 à 5 étoiles
- **Commentaires** — Commentez et répondez avec un système hiérarchique
- **Signalement** — Signalez un contenu inapproprié (spam, fausses données, autre)

---

## Prérequis techniques

- Navigateur récent (Firefox, Chrome, Safari, Edge)
- Connexion internet
- **Un client torrent** (qBittorrent, Transmission, Deluge) pour télécharger les données volumineuses via magnet links
- **Compréhension du P2P** : Les données sont distribuées via le réseau BitTorrent. Lorsque vous téléchargez, vous participez automatiquement à la redistribution, renforçant la disponibilité des données pour la communauté.
- **Espace disque** : Variable selon les packs téléchargés. Les packs sont des fichiers GeoPackage (.gpkg) pouvant atteindre plusieurs gigaoctets.

---

## Types de données supportés

| Type | Description |
|------|-------------|
| Géodonnées | Fichiers SIG, shapefiles, GeoJSON, CSV, GPKG |
| Cartes | Produits cartographiques, tuiles, cartes interactives |
| Applications | Services web, outils géospatiaux, dashboards, visualisations |

## Formats disponibles

- **Simples** : fichiers unitaires contenant une seule couche de données (ex: un CSV, un GeoJSON simple, un shapefile). Distribués exclusivement via magnet link. Idéal pour un fichier unique sans organisation multi-couche.
- **Packs (GeoPackage)** : fichiers uniques au format `.gpkg` (standard OGC) contenant plusieurs couches de données organisées par thématique. Distribués exclusivement via magnet link. Idéal pour les collections SIG complètes avec styles QML intégrés.
- **Individuels** : fichiers unitaires multiples (gpkg, csv, shp, geojson, kml, gml, gpx, topojson, geoparquet, tab, xml). Distribués obligatoirement via magnet link.

> **Pour une comparaison détaillée entre fichiers simples, packs et fichiers individuels**, consultez la page [Simple, Pack (GeoPackage) vs Individuel](/docs/pack-vs-individuel).

Taille maximale de fichier : Aucune, car les données sont distribuées par Torrent et non stockées sur le serveur.

---

## Profil public

Chaque utilisateur dispose d'un profil public accessible via `/profile/<id>`, affichant ses publications, ses organisations, et son activité.

## Pages statiques

- `/mentions-legales` — Mentions légales
- `/confidentialite` — Politique de confidentialité
- `/cgu` — Conditions d'utilisation