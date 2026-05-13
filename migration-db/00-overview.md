# Plan de Migration : Mock Data → PostgreSQL 18

## Vue d'ensemble

Remplacer les ~600 items mock (générés au démarrage dans `app.py`) par des données persistantes en PostgreSQL 18.

---

## Ordre d'exécution recommandé

```
Phase 1 (config) → Phase 2 (modèles) → Phase 3 (migration)
      ↓
Phase 4 (seed data) → Phase 5 (refactor app.py) → Phase 6 (auth/rating/comments/reports/bans)
      ↓
Phase 7 (tests) → Phase 8 (nettoyage)
```

## Fichiers à créer/modifier

| Action | Fichier |
|--------|---------|
| **Modifier** | `requirements.txt` (ajout deps : SQLAlchemy, psycopg2, Flask-Migrate) |
| **Modifier** | `.env.example` (ajout DATABASE_URL) |
| **Modifier** | `app.py` (suppression mock + injection DB, ~150 lignes modifiées) |
| **Modifier** | `models.py` → **créer** (modèles ORM incluant chunks + viz_links) |
| **Créer** | `scripts/seed_data.py` (peuplement initial de la BDD) |
| **Créer** | `workers/processing.py` (worker Celery pour traitement des uploads) |
| **Optionnel** | `scripts/init_db.py` (initialisation automatique) |

---

## Points d'attention

1. **Compatibilité templates** : Les templates Jinja attendent des dicts avec les clés exactes (`id`, `title`, `format`, `tags`, `gallery`, etc.). La méthode `to_dict()` doit reproduire cette structure exacte.
2. **Performance** : Ajouter un index sur `items(magnet_link)` pour éviter les doublons de magnet link.
3. **Migrations** : Si le projet évolue (ajout de colonnes), utiliser Flask-Migrate/Alembic plutôt que des ALTER TABLE manuels.
4. **Sécurité** : Les mots de passe doivent être hashés avec `werkzeug.security.generate_password_hash` et vérifiés avec `check_password_hash`.
5. **Rollback plan** : Avant la migration, exporter les données mock dans un fichier JSON (`python -c "import json; ..."`), au cas où il faudrait revenir en arrière.
6. **Upload de chunks** : Un chunk uploadé doit passer par une validation avant d'être `is_published=True`. Tant que le statut n'est pas `"published"`, il n'apparaît pas dans le catalogue public.
7. **Onglet Visualisation** : Les liens sont stockés séparément des items (table `visualization_links`). L'affichage se fait via `item.visualization_links` en relation N-N. Chaque utilisateur peut ajouter ses propres liens qui apparaissent à côté des liens officiels du système.
8. **Espace de stockage** : Prévoir un volume Docker pour `/uploads/` ou configurer S3-compatible storage (MinIO) pour les fichiers uploadés par les utilisateurs.
9. **Vérification de confiance** : `verification_status` gère deux états principaux — `pending` (données **pleinement visibles et accessibles**, juste pas encore vérifiées par le site) et `verified` (données approuvées = **confiance officielle du site**). Un état `rejected` existe mais est réservé à des cas de non-conformité grave ; en usage normal, toutes les données restent visibles.
10. **Endpoint de vérification** : `/api/items/<id>/verify` doit être protégé par un rôle (admin/reviewer). Un utilisateur normal ne peut pas se marquer lui-même comme vérifié.
11. **Organisations / Groupes** : `organizations` + `organization_members` permettent aux utilisateurs de s'associer à des groupes/organisations. Les items/chunks uploadés peuvent être associés à une organisation (`organization_id`). La hiérarchie des rôles dans les organisations est : `member < editor < admin < owner`. L'owner peut transférer son rôle avant de quitter l'organisation. Un utilisateur peut appartenir à plusieurs organisations simultanément.
12. **Signalements (reports)** : `reports` permet aux utilisateurs de signaler un utilisateur, une donnée, une carte ou une application. Les admins consultent et clôturent les signalements (`pending` → `resolved` / `dismissed`). Un utilisateur ne peut pas se signer lui-même. Le statut n'entraîne **aucune suppression automatique** — l'admin décide de la suite (ban, warning, etc.).
13. **Bans** : `banned BOOLEAN DEFAULT FALSE` sur les utilisateurs. Un utilisateur banni est déconnecté et ne peut plus accéder à l'application. Le ban se fait depuis le panel admin et ne supprime pas les données publiées par l'utilisateur.

---

## Structure du plan

| Fichier | Contenu |
|---------|---------|
| `01-prerequis-configuration.md` | Phase 1 — Prérequis & Configuration |
| `02-modelisation-base-donnees.md` | Phase 2 — Modélisation de la Base de Données |
| `03-initialisation-migrations.md` | Phase 3 — Initialisation & Migrations |
| `04-seed-data.md` | Phase 4 — Seed Data (Peuplement de la BDD) |
| `05-refactor-app.md` | Phase 5 — Refactorisation de app.py |
| `06-auth-interactions.md` | Phase 6 — Fonctionnalités Auth & Interactions |
| `07-tests-validation.md` | Phase 7 — Tests & Validation |
| `08-nettoyage-final.md` | Phase 8 — Nettoyage Final |
| `09-upload-chunks-visualisation.md` | Phase 9 — Upload de Chunks & Liens de Visualisation |
| `10-securite-prevention-failles.md` | Phase 10 — Sécurité & Prévention des Failles |
| `06-auth-interactions.md` (ajouté) | Phase 6 — Banning + Système de signalements (reports) |
