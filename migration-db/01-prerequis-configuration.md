# Phase 1 — Prérequis & Configuration

### 1.1 Ajouter les dépendances Python
**Fichier :** `requirements.txt`

Ajouter :
- `SQLAlchemy>=2.0` — ORM
- `Flask-SQLAlchemy>=3.1` — intégration SQLAlchemy + Flask
- `psycopg2-binary>=2.9` — driver PostgreSQL (développement)
- `Flask-Migrate>=4.0` — migrations Alembic

### 1.2 Configurer la connexion DB dans `.env.example`
Ajouter les variables existantes en commentaire :
```
DATABASE_URL=postgresql://ananas_user:mot_de_pass e@postgres:5432/ananas
SQLALCHEMY_DATABASE_URI=postgresql://ananas_user:mot_de_pass e@postgres:5432/ananas
SQLALCHEMY_ENGINE_OPTIONS=json {"pool_pre_ping": true}
```

### 1.3 Vérifier docker-compose.yml
La configuration est correcte : `postgres:18-alpine` sur port 5432, volume `pg_data` persistant. Aucune modification requise.
