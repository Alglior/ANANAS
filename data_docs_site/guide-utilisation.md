# Guide d'utilisation

Bienvenue sur **A.N.A.N.A.S.** — *Atlas Numerique d'Archives de Noeuds et d'Acces Synchronises*, une plateforme de diffusion de données géospatiales via des protocoles décentralisés (BitTorrent / magnet links).

---

## Fonctionnalités principales

### Catalogue de données
Trois catalogues distincts sont disponibles :

- **Données** (`/catalogue/donnees`) — Fichiers SIG, shapefiles, GeoJSON, CSV géoréférencés
- **Cartes** (`/catalogue/cartes`) — Produits cartographiques, tuiles, fonds de carte
- **Applications** (`/catalogue/applications`) — Services web, outils géospatiaux, widgets

Chaque catalogue est paginé (30 éléments par page) et propose des filtres par statut de vérification (vérifié / non officiel), organisation, et niveau de format (individuel / pack). Accès JSON possible via `/catalogue/<type>/<page>/json`.

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
- **Sécurité** — Changer votre mot de passe (invalide les sessions existantes)
- **Activité** — Historique de vos notes, commentaires, publications
- **Organisations** — Vos organisations et rôles

### Publication de données

1. Rendez-vous sur `/upload`
2. Remplissez les métadonnées (titre, description, type, format, licence)
3. Ajoutez un lien magnet ou téléchargez un fichier
4. Ajoutez des tags et des liens de visualisation
5. Publiez ou sauvegardez comme brouillon

Les brouillons et la corbeille sont accessibles depuis la page de publication.

### Organisations

Les organisations permettent de collaborer autour de jeux de données :

- **Créer** une organisation avec un slug unique
- **Inviter** des membres par email
- **Gérer les rôles** : membre, modérateur, éditeur, admin, propriétaire
- **Rôles personnalisés** avec permissions granulaires (inviter, supprimer des membres, éditer, gérer les éléments, modérer, gérer les rôles, supprimer l'organisation)

### Interactions

- **Notation** — Notez les éléments de 1 à 5 étoiles
- **Commentaires** — Commentez et répondez avec un système hiérarchique
- **Signalement** — Signalez un contenu inapproprié (spam, fausses données, autre)

---

## Prérequis techniques

- Navigateur récent (Firefox, Chrome, Safari, Edge)
- Connexion internet
- Un client torrent (qBittorrent, Transmission, etc.) pour télécharger les données lourdes via magnet links

---

## Types de données supportés

| Type | Description |
|------|-------------|
| Géodonnées | Fichiers SIG, shapefiles, GeoJSON, CSV, GPKG |
| Cartes | Produits cartographiques, tuiles, cartes interactives |
| Applications | Services web, outils géospatiaux, dashboards, visualisations |

## Formats disponibles

- **Packs** : archives complètes distribuées via magnet link (zip, tar.gz)
- **Individuels** : fichiers unitaires (csv, shp, geojson, gpkg, json, xml, png, jpg, gif, svg, pdf)

Taille maximale de fichier uploadé : Aucune car les fichiers sont du Torrent.

---

## Profil public

Chaque utilisateur dispose d'un profil public accessible via `/profile/<id>`, affichant ses publications, ses organisations, et son activité.

## Pages statiques

- `/mentions-legales` — Mentions légales
- `/confidentialite` — Politique de confidentialité
- `/conditions-utilisation` — Conditions d'utilisation