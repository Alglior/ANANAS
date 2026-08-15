# Contribution

Comment contribuer au projet **A.N.A.N.A.S.** et participer à la diffusion de données géospatiales.

---

## Signaler un bug

Vous avez rencontré un bug ? Utilisez le formulaire de contact disponible sur `/contact` ou ouvrez une issue sur le dépôt officiel du projet.

## Proposer une amélioration

Toute suggestion est bienvenue. Décrivez votre idée via le formulaire de contact (`/contact`) en précisant le sujet et les détails de votre proposition.

## Publier des données

### Création de compte

Avant de publier, vous devez créer un compte :

1. Rendez-vous sur `/inscription`
2. Renseignez votre prénom, nom et mot de passe
3. Un pseudo unique vous est automatiquement attribué (ex: `john-doe#ab7f3c`)
4. Connectez-vous sur `/connexion`

### Publication

1. Connectez-vous à votre compte
2. Accédez à `/upload`
3. Remplissez les métadonnées obligatoires :
   - Titre
   - Description
   - Type (donnée, carte ou application)
   - Format
   - **Lien magnet** (obligatoire — les données ne sont pas hébergées sur le serveur)
4. Choisissez le **niveau de format** :
   - **Simple** : fichier unique avec une seule couche (ex: un CSV, un GeoJSON) — distribué exclusivement par magnet link
   - **Pack** : fichier GeoPackage (.gpkg) multi-couches — distribué exclusivement par magnet link
   - **Individuel** : plusieurs fichiers distincts — distribué obligatoirement par magnet link
5. Ajoutez des images via magnet links (optionnel — pour la galerie)
6. Ajoutez un lien magnet pour la documentation PDF (optionnel — améliore le score IMOD de +2 points)
7. Ajoutez un lien de visualisation externe (optionnel — WMS, WFS, dashboard)
8. Ajoutez des tags et choisissez une licence
9. Associez à une organisation (optionnel)
10. Publiez ou sauvegardez comme brouillon

**Options avancées** :
- **Import JSON en masse** : déposez un ou plusieurs fichiers JSON pour créer plusieurs items d'un coup
- **Script Python** : utilisez le script de publication en masse inclus dans l'interface
- **Score IMOD** : aperçu en temps réel de la qualité de vos métadonnées (score /100)

> **Important — Modèle de distribution P2P** : A.N.A.N.A.S. n'héberge **aucune donnée** sur son serveur. La plateforme est un catalogue d'indexation : seuls les métadonnées et les liens magnet sont stockés. Les données réelles circulent exclusivement sur le réseau BitTorrent entre les pairs. Sans lien magnet valide, la publication est impossible. Assurez-vous que votre client torrent reste actif (en *seed*) après publication pour garantir la disponibilité des données.

### Gestion des publications

- **Brouillons** — Accessibles depuis `/brouillons` ou l'onglet brouillons de `/upload`
- **Corbeille** — Les éléments supprimés sont placés en corbeille (récupérables)
- **Suppression définitive** — Possible depuis la corbeille

### Bonnes pratiques P2P pour les éditeurs

- **Seeding** : Après avoir publié un magnet link, gardez votre client torrent ouvert au moins jusqu'à ce qu'un ratio de 1:1 soit atteint
- **Doublons** : Avant de publier, vérifiez dans le catalogue que les données n'existent pas déjà
- **Métadonnées** : Remplissez des tags précis et une description complète pour faciliter le filtrage
- **Organisation** : Associez vos données à une organisation pour crédibiliser la source et permettre la gestion collective

## Rejoindre une organisation

1. Parcourez les organisations sur `/organizations`
2. Cliquez sur une organisation pour voir ses détails
3. Cliquez sur "Rejoindre"
4. Un administrateur de l'organisation peut également vous inviter par email

### Rôles disponibles

| Rôle | Permissions |
|------|-------------|
| Membre | Aucune permission particulière |
| Modérateur | Supprimer des membres, modérer le contenu |
| Éditeur | Gérer les éléments |
| Admin | Inviter/supprimer des membres, éditer l'org, gérer les éléments, modérer |
| Propriétaire | Toutes les permissions incluant la gestion des rôles et la suppression |

## Modération

Les contenus publiés sont modérés par les administrateurs de la plateforme pour garantir :

- La qualité des données partagées
- La légalité des contenus
- Le respect des conditions d'utilisation

Les éléments peuvent être vérifiés (statut `verified`), marqués comme non officiels (`unofficial`) ou rejetés (`rejected`).

## Signalement

Si vous rencontrez un contenu inapproprié :

1. Connectez-vous à votre compte
2. Ouvrez la page de l'élément concerné
3. Utilisez le bouton de signalement
4. Choisissez la raison (spam, fausses données, autre)
5. Ajoutez une description optionnelle

## Développement

### Stack technique

- **Backend** : Python / Flask 3.1 / SQLAlchemy 2.x
- **Base de données** : PostgreSQL 18
- **Frontend** : Jinja2 / CSS vanilla modulaire / JavaScript vanilla
- **Conteneurisation** : Docker / Docker Compose
- **Proxy** : Nginx
- **Client torrent** : qBittorrent (cache d'images)

### Installation locale

```bash
git clone <url-du-depot>
cd sitev2
./setup.sh
```

### Tests

```bash
pytest tests/
```

### Architecture

Le projet suit une architecture Flask classique avec blueprints :

- `src/auth_routes.py` — Authentification
- `src/catalogue_routes.py` — Catalogue
- `src/item_routes.py` — Détail des éléments
- `src/interactions.py` — Notes, commentaires, signalements
- `src/organization_routes.py` — Organisations
- `src/user_routes.py` — Profils, upload, brouillons
- `src/contact_routes.py` — Formulaire de contact
- `src/privacy_routes.py` — Politique de confidentialité
- `src/legal_routes.py` — Mentions légales
- `src/tos_routes.py` — Conditions d'utilisation
- `src/doc_routes.py` — Documentation (Markdown)
- `src/index_routes.py` — Route d'accueil dynamique
- `src/admin/` — Panneau d'administration (14 sous-modules)
- `src/image_cache.py` — Cache d'images depuis magnet links
- `models.py` — 20 modèles SQLAlchemy