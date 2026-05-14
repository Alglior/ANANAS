# Plan d'Audit de Sécurité — A.N.A.N.A.S.

## 1. POSTGRESQL 18 (Base de données)

### 🔴 CRITIQUE

**1.1 Chiffrement SSL/TLS pour la connexion DB**
- **Fichier**: `docker-compose.yml`, `.env`
- **Problème**: La connexion entre l'app et PostgreSQL n'utilise pas SSL (`sslmode=require` manquant)
- **Risque**: Interceptation des credentials en transit dans le réseau Docker
- **Fix**: Ajouter `?sslmode=require` à `SQLALCHEMY_DATABASE_URI`

**1.2 Limitation de connexions DB (max_connections)**
- **Fichier**: `docker-compose.yml`
- **Problème**: PostgreSQL utilise la valeur par défaut (habituellement 100)
- **Risque**: Attaques par déni de service sur la DB
- **Fix**: Configurer `POSTGRES_INITDB_EXTRA_OPTS='--max-connections=50'` dans docker-compose

**1.3 Rôle PostgreSQL restreint**
- **Fichier**: `docker-compose.yml`, scripts SQL init
- **Problème**: `ananas_user` a probablement un accès complet à tous les schemas/tables
- **Fix**: Créer un rôle spécifique avec `GRANT SELECT, INSERT, UPDATE ONLY sur les tables nécessaires (pas de DROP/ALTER/TRUNCATE)

### 🟡 MODÉRÉ

**1.4 Journalisation PostgreSQL**
- **Fichier**: `docker-compose.yml`
- **Fix**: Ajouter `POSTGRES_LOG_MIN_STATEMENT=ddl`, `POSTGRES_LOG_CONNECTIONS=true` pour tracer les accès suspects

---

## 2. AUTHENTIFICATION & SESSIONS

### 🔴 CRITIQUE

**2.1 Politique de complexité des mots de passe**
- **Fichier**: `src/auth_routes.py:49`
- **Problème**: Aucune validation de la force du mot de passe lors de l'inscription
- **Fix**: Ajouter un minimum de 8 caractères + complexité (majuscule, chiffre, caractère spécial)

### 🔴 CRITIQUE

**2.2 Rate limiting spécifique sur `/connexion`**
- **Fichier**: `app.py:33`
- **Problème**: Le limiter global `"100 per hour"` est trop permissif pour le login
- **Fix**: Ajouter `@limiter.limit("5 per hour")` spécifiquement sur `/connexion`

### 🟡 MODÉRÉ

**2.3 Durée de session**
- **Fichier**: `app.py:89`
- **Problème**: 1 heure (`PERMANENT_SESSION_LIFETIME = 3600`) — acceptable mais prolongé pour des données géosensibles
- **Fix**: Réduire à `1800` (30 min)

---

## 3. VULNÉRABILITÉS APPLICATION

### 🔴 CRITIQUE

**3.1 Bug `dt.datetime.now` vs `dt.datetime.now()`**
- **Fichier**: `src/interactions.py:76`
- **Problème**: `item.verified_at = dt.datetime.now` — la fonction est assignée, pas appelée (manque parenthèses)
- **Fix**: `item.verified_at = datetime.datetime.now()`

### 🔴 CRITIQUE

**3.2 CSRF non appliqué aux endpoints API JSON**
- **Fichiers**: `app.py`, `src/interactions.py`, `src/admin_routes.py`, `src/upload_routes.py`
- **Problème**: Flask-WTF protège les formulaires HTML mais pas les requêtes AJAX fetch()
- **Fix**: Vérifier le token CSRF dans un header (ex: `X-CSRF-Token`) pour toutes les routes API en POST

### 🟡 MODÉRÉ

**3.3 Validation du contenu des fichiers uploadés (Magic Bytes)**
- **Fichier**: `src/upload_routes.py:14-18`
- **Problème**: Seule l'extension est vérifiée — un fichier `.exe` renommé en `.csv` passerait
- **Fix**: Vérifier le magic number / MIME type réel avec `file.mimetype` et/ou bibliothèques (ex: `python-magic`)

### 🟡 MODÉRÉ

**3.4 Limite de taille d'upload**
- **Fichier**: `app.py` (ajout config)
- **Problème**: Aucune limite de taille de fichier
- **Fix**: Ajouter `app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024` (10 Mo max)

### 🟡 MODÉRÉ

**3.5 Endpoint JSON catalogue ne filtre pas les items non publiés**
- **Fichier**: `src/catalogue_routes.py:125`
- **Problème**: Le endpoint JSON utilise `Item.query.filter_by(type=item_type)` sans filtrer `is_published=True`
- **Fix**: Ajouter `.filter_by(is_published=True)` dans le endpoint JSON

---

## 4. CONTRÔLE D'ACCÈS & AUTORISATION

### 🟡 MODÉRÉ

**4.1 Vérification admin avec `hasattr()` au lieu d'une méthode/explicit check**
- **Fichier**: `src/admin_routes.py:16,42,114` (etc.)
- **Problème**: `if not hasattr(current_user, "is_admin")` est fragile
- **Fix**: Utiliser `if not current_user.is_admin:` directement

---

## 5. SÉCURITÉ HTTP & FRONT-END

### 🟡 MODÉRÉ

**5.1 Header X-XSS-Protection déprécié**
- **Fichier**: `app.py:64`
- **Problème**: Ce header est déprécié dans les navigateurs modernes
- **Fix**: Supprimer la ligne ou remplacer par un avertissement

---

## 6. DOCKER & INFRASTRUCTURE

### 🟡 MODÉRÉ

**6.1 Health check pour PostgreSQL**
- **Fichier**: `docker-compose.yml`
- **Problème**: `depends_on: postgres` attend juste le démarrage du container, pas la disponibilité de PostgreSQL
- **Fix**: Ajouter un `healthcheck` avec `pg_isready` au service postgres

### 🟡 MODÉRÉ

**6.2 Build Docker en non-root pour COPY**
- **Fichier**: `Dockerfile`
- **Problème**: Le `COPY . .` se fait en root
- **Fix**: Utiliser multi-stage build ou déplacer le USER avant COPY

---

## 7. RANGING GLOBAL DES PRIORITÉS

| Priorité | Problème | Fichier(s) | Effort estimé |
|----------|----------|------------|---------------|
| 🔴 P0 | SSL requis pour connexion DB | docker-compose.yml, .env | 15min |
| 🔴 P0 | Rate limiting sur /connexion | app.py | 15min |
| 🔴 P0 | CSRF token pour API JSON | app.py, interactions.py, admin_routes.py, upload_routes.py | 30min |
| 🔴 P0 | Bug `dt.datetime.now` sans parenthèses | src/interactions.py:76 | 5min |
| 🟡 P1 | Politique de complexité mot de passe | src/auth_routes.py | 20min |
| 🟡 P1 | Validation du contenu des fichiers uploadés (magic bytes) | src/upload_routes.py | 30min |
| 🟡 P1 | Limite de taille d'upload (MAX_CONTENT_LENGTH) | app.py | 5min |
| 🟡 P1 | Endpoint JSON catalogue ne filtre pas is_published=True | src/catalogue_routes.py | 10min |
| 🟡 P1 | Health check docker-compose pour postgres | docker-compose.yml | 10min |
| 🟡 P1 | Restriction du rôle PostgreSQL (GRANT sélectif) | docker-compose.yml | 15min |
| 🟡 P2 | Header X-XSS-Protection déprécié | app.py:64 | 2min |
| 🟢 Info | Durée de session (réduire à 30 min) | app.py:89 | 2min |
| 🟢 Info | Health check pour PostgreSQL (pg_isready) | docker-compose.yml | 10min |

---

## Résumé des actions rapides (5 minutes)

1. **`src/interactions.py:76`**: Ajouter `()` à `datetime.datetime.now()`
2. **`app.py:64`**: Supprimer le header `X-XSS-Protection` déprécié
3. **`app.py:89`**: Réduire `PERMANENT_SESSION_LIFETIME` de `3600` à `1800`

## Résumé des actions critiques (30-60 minutes)

4. **Rate limiting sur `/connexion`**: Ajouter `@limiter.limit("5 per hour")`
5. **CSRF pour API JSON**: Vérifier le token dans un header custom pour les routes API
6. **SSL pour DB PostgreSQL**: Ajouter `?sslmode=require` aux URIs de connexion
