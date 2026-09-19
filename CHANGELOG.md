# Mises à jour

> **Note** : la version **1.0 (Septembre 2026)** est la **première version bêta** de la plateforme A.N.A.N.A.S. L'ensemble des fonctionnalités ci-dessous a été développé et affiné depuis le début du projet (avril 2026).

## v1.0.1 — Septembre 2026

### Nouvelles fonctionnalités
- Page « Feuille de route » (`/feuille-de-route`) présentant les fonctionnalités en cours, planifiées et les visions long terme
- Menu « Mise à jour » dans la barre de navigation regroupant le journal des mises à jour et la feuille de route

### Améliorations
- Documentation de l'API enrichie et alignée avec l'ensemble des endpoints réellement exposés (méthodes corrigées, endpoints manquants ajoutés)

---

## v1.0.0 — Bêta — Septembre 2026

### Catalogue & données
- **Multi-catalogues** : données, cartes, applications
- **Pagination** + export JSON (`/catalogue/<type>/<page>/json`)
- **Recherche avancée** par étiquettes (`/catalogue/<type>/recherche-avancee`)
- **Filtres** par statut de vérification, organisation et niveau de format
- **Niveaux de format** : simple, pack (GeoPackage), individuel (chunks)
- **Score de qualité IMOD** (métadonnées 45 %, technique 36 %, richesse 19 %)
- **Fiche élément** : galerie, liens magnet par échelle, onglets données/visualisation, documentation PDF, vidéo tutoriel, liens magnet pour images
- **Fichiers simples** mis en avant sur l'accueil (sélection admin)

### Publication
- Formulaire d'upload complet avec **lien magnet obligatoire** (les données ne sont jamais hébergées sur le serveur)
- **Niveaux de format** : simple / pack GeoPackage / individuel
- **Import JSON en masse** et script Python de publication
- **Brouillons**, **corbeille** et suppression définitive (purge)
- Publication et suppression **en masse** des brouillons / publications
- Vérification de ses publications (admin)
- Métadonnées enrichies : année de données, taille, licence, organisation, tags

### Comptes & authentification
- Inscription avec **pseudo auto-généré** unique (`prenom-nom-xxxx#1234`)
- Connexion sécurisée avec **rate limiting** anti-brute-force
- **Authentification à deux facteurs (2FA / TOTP)** avec QR code
- **Codes de récupération** (usage unique)
- **Profil public** (`/profile/<id>`) avec publications et activité
- **Tableau de bord compte** (`/compte`) : informations, sécurité, activité
- Changer son mot de passe (invalide les sessions existantes)
- **Avatar** personnalisé (png/jpg/webp)

### Organisations
- Création d'organisations avec slug unique
- Adhésion avec **demandes d'accès** (approbation / refus)
- **Invitation par pseudo**
- **Rôles** : membre, modérateur, éditeur, admin, propriétaire + **rôles personnalisés** à permissions granulaires
- Pages publiques d'organisation + listing des items par organisation
- **Réplication de catalogue distant** (aperçu + récupération)
- Suppression d'organisation

### Interactions
- **Notation 1–5 étoiles**
- **Commentaires threadés** avec réponses
- **Signalements** (spam, fausses données, autre)

### Administration
- **Panneau d'administration** complet :
  - Utilisateurs : ban / deban / tempban / mute / warn / kick
  - **Modération** des items et commentaires (filtres par statut, vérification)
  - **Journal d'audit**
  - **Messages de contact**
- **Sites miroirs**
- **Éléments à la une** (featured)
- **Packs GeoPackage**
- **Tags prédéfinis** (catégories et tags)
- **Fichiers simples**
- **Activation / désactivation** des catalogues
- **Paramètres du site** : accueil, maintenance, inscriptions, pagination
- **Sauvegarde / restauration** de la base de données
- **Interface qBittorrent** : suivi des transferts et des torrents, nettoyage des torrents orphelins
- **Édition de la page des mises à jour**

### P2P & images
- Distribution **BitTorrent / magnet links** (aucune donnée stockée sur le serveur)
- **Téléchargement d'images via torrent (DHT)** avec suivi par aimant (statut, progression)
- **Cache d'images** asynchrone (TTL 30 jours) via qBittorrent
- Nettoyage automatique des torrents et du cache à la suppression d'un élément

### Documentation & pages
- **Documentation intégrée** (rendu Markdown) : guide d'utilisation, P2P & BitTorrent, formats, organisation des données, contribution
- **Documentation API interactive** (`/api`) : endpoints, méthodes, exemples curl / python / javascript
- **Rapports PDF** (`/rapport`)
- **Journal des mises à jour** (`/changelog`) et **Feuille de route** (`/feuille-de-route`)
- Pages statiques : À propos, mentions légales, conditions d'utilisation, confidentialité
- **Version mobile / responsive** (hamburger menu, breakpoints tablette & mobile)

### Technique & sécurité
- Architecture **Flask / blueprints** modulaires (17 blueprints)
- **PostgreSQL 18** + SQLAlchemy, migrations Alembic
- **Docker Compose** : nginx, app (Gunicorn), PostgreSQL, Redis, qBittorrent
- **Protection CSRF** globale (Flask-WTF + en-tête `X-CSRF-Token` sur l'API)
- **Headers de sécurité** : CSP nonce-based, HSTS, X-Frame-Options, X-Content-Type-Options
- **Rate limiting** (Flask-Limiter + Redis)
- **Sanitisation HTML** (bleach) et validation des entrées
- **Validation des magnet links** et des URLs externes
- **Cookies de session** sécurisés (HTTP-only, SameSite=Strict) et durée de session 30 min
- **Mode maintenance** configurable