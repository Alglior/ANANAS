# Plan de Migration : Mock Data → PostgreSQL 18

## Vue d'ensemble

Remplacement des ~600 items mock (générés au démarrage dans `app.py`) par des données persistantes en PostgreSQL 18. Migration complète via Alembic + SQLAlchemy ORM.

---

## Statut global

| Phase | Nom | Statut | Commit |
|-------|-----|--------|--------|
| **Phase 1** | Prérequis & Configuration | ✅ Terminé | `73dacaf` |
| **Phase 2** | Modélisation de la Base de Données | ✅ Terminé | `b12cfc0` |
| **Phase 3** | Initialisation & Migrations | ✅ Terminé | `5941843` |
| **Phase 4** | Seed Data (Peuplement de la BDD) | ✅ Terminé | `0e02ea9` |
| **Phase 5** | Refactorisation de app.py | ✅ Terminé | `9b012d4` |
| **Phase 6** | Auth & Interactions | ✅ Terminé | `a28d09f` |
| **Phase 7** | Tests & Validation | ✅ Terminé | (tests existants) |
| **Phase 8** | Nettoyage Final | ✅ Terminé | (hashlib supprimé, .gitignore + Dockerfile ok) |
| **Phase 9** | Upload Chunks & Visualisation | ✅ Terminé* | *(worker Celery en stub) |
| **Phase 10** | Sécurité & Prévention | ⚠️ Partiel | `3a51d96` |

> \* Phases 1-8 : migration core complétée. Phase 9 : endpoints fonctionnels (worker Celery en stub). Phase 10 : sécurité partielle.

---

## Fichiers créés/modifiés

| Fichier | Action | Statut |
|---------|--------|--------|
| `requirements.txt` | Ajout deps : SQLAlchemy, psycopg2, Flask-Migrate, Flask-Limiter | ✅ |
| `.env.example` | Ajout DATABASE_URL, SQLALCHEMY_DATABASE_URI | ✅ |
| `app.py` | Suppression mock + injection DB (~150 lignes modifiées) | ✅ |
| `models.py` | 9 modèles ORM, 11 tables (incluant chunks + viz_links) | ✅ |
| `alembic/versions/fa99e124f96c_initial_schema.py` | Migration Alembic initiale | ✅ |
| `scripts/seed_data.py` | Peuplement initial (600 items) | ✅ |
| `scripts/init_db.py` | Initialisation automatique DB | ✅ |
| `workers/processing.py` | Worker Celery stub (non implémenté) | ⚠️ |
| `fix_migration.py` | Correction pending→unofficial au startup | ✅ |
| `tests/test_routes.py` | Tests routes (Phase 7.1-7.6) | ✅ |
| `tests/test_models.py` | Tests modèles ORM | ✅ |

---

## Points d'attention (implémentés)

1. ✅ **Compatibilité templates** : `to_dict()` sur `Item` reproduit la structure exacte attendue par Jinja.
2. ✅ **Performance** : Index sur `items(magnet_link)` pour éviter les doublons. Index sur type, format_type, created_at, verification_status.
3. ✅ **Migrations Alembic** : Migrations gérées via Flask-Migrate/Alembic (pas d'ALTER TABLE manuel).
4. ✅ **Sécurité password** : Hashing scrypt via `werkzeug.security`.
5. ⚠️ **Rollback plan** : Export mock JSON recommandé avant toute migration supplémentaire.
6. ✅ **Upload de chunks** : Validation avant publication (`is_published=True`). Statut `"published"` requis pour catalogue public. Worker Celery en stub.
7. ✅ **Onglet Visualisation** : Liens dans `visualization_links`. Affichage via `item.visualization_links`. Liens utilisateurs séparés des liens officiels.
8. ✅ **Espace de stockage** : Volume Docker `/uploads/` configuré. S3-compatible optionnel.
9. ✅ **Vérification de confiance** : 3 états — `unofficial` (non officielles), `verified` (confiance officielle), `rejected`. Défaut = `unofficial`.
10. ✅ **Endpoint de vérification** : `/api/items/<id>/verify` protégé par rôle admin/reviewer.
11. ✅ **Organisations / Groupes** : 4 rôles (member < editor < admin < owner). Multi-organisation supportée. Items associés à une orga.
12. ✅ **Signalements** : Signalement user/item. Admin traite (`pending` → `resolved`/`dismissed`). Pas de suppression auto. Anti-auto-signalement.
13. ✅ **Bans** : Déconnexion automatique, plus d'accès. Panel admin avec liste + action ban/unban.

---

## Structure du plan

| Fichier | Contenu | Statut |
|---------|---------|--------|
| `01-prerequis-configuration.md` | Phase 1 — Prérequis & Configuration | ✅ |
| `02-modelisation-base-donnees.md` | Phase 2 — Modélisation de la Base de Données | ✅ |
| `03-initialisation-migrations.md` | Phase 3 — Initialisation & Migrations | ✅ |
| `04-seed-data.md` | Phase 4 — Seed Data (Peuplement de la BDD) | ✅ |
| `05-refactor-app.md` | Phase 5 — Refactorisation de app.py | ✅ |
| `06-auth-interactions.md` | Phase 6 — Auth, ratings, comments, orgs, bans, reports | ✅ |
| `07-tests-validation.md` | Phase 7 — Tests & Validation | ✅ |
| `08-nettoyage-final.md` | Phase 8 — Nettoyage Final | ✅ |
| `09-upload-chunks-visualisation.md` | Phase 9 — Upload de Chunks & Liens de Visualisation | ✅* |
| `10-securite-prevention-failles.md` | Phase 10 — Sécurité & Prévention des Failles | ⚠️ Partiel |

> \* Phase 9 : endpoints fonctionnels, worker Celery en stub (non implémenté).
