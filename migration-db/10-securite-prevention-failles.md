# Phase 10 — Sécurité & Prévention des Failles

### 10.1 Protection contre les injections SQL (primary defense)

**SQLAlchemy ORM est la première ligne de défense.** Tous les requêtes passent par l'ORM qui fait l'escaping automatique :

```python
# SÛR — SQLAlchemy ORM (parameterized queries automatiques)
User.query.filter_by(prenom=prenom, nom=nom).first()  # ← pas d'injection possible

# À ÉVITER ABSOLUMENT : requêtes string brutes
db.session.execute(f"SELECT * FROM users WHERE prenom = '{prenom}'")  # ← VULNÉRABLE
```

**Si vous devez utiliser du SQL brut :**
```python
from sqlalchemy import text

# JAMAIS f-string pour les valeurs — utiliser params={}
stmt = text("SELECT * FROM users WHERE prenom = :prenom AND nom = :nom")
result = db.session.execute(stmt, {"prenom": prenom, "nom": nom})
```

### 10.2 CSRF (Cross-Site Request Forgery) — DÉJÀ ACTIF ✅

Flask-WTF CSRFProtect est déjà configuré dans `app.py`. **Ne pas le désactiver.**

```python
# app.py — garanti existant, NE PAS MODIFIER :
csrf = CSRFProtect(app)  # ← protège tous les formulaires POST
```

**Chaque formulaire doit avoir le token CSRF :**
```html
<!-- templates/connexion.html -->
<form method="POST" action="/connexion">
    {{ form.csrf_token }}  {# Flask-WTF ajoute automatiquement #}
    <input name="prenom" placeholder="Prénom">
    <input name="nom" placeholder="Nom">
    <input type="password" name="password">
    <button type="submit">Se connecter</button>
</form>
```

### 10.3 XSS (Cross-Site Scripting) — templates Jinja auto-échappent ✅

Jinja2 échape automatiquement toutes les variables : `{{ user.nom }}` → `" &lt;script&gt;...`.

**Quand il faut désactiver l'échappement (rare, cas spécifique) :**
```html
<!-- ❌ DANGEREUX — n'utilisez JAMAIS sans confiance absolue -->
{{ variable | safe }}

<!-- ✅ SÛR — si vous devez afficher du HTML, utiliser bleach -->
{% raw %}{{ variable }}{% endraw %}  {# échappé automatiquement #}
```

**Bibliothèque de nettoyage pour les champs utilisateurs :**
```python
# requirements.txt — ajouter :
# bleach>=6.0

import bleach

def sanitize_input(user_input: str) -> str:
    """Nettoyer les entrées utilisateur pour prévenir XSS."""
    return bleach.clean(
        user_input,
        tags=[],           # aucun tag HTML autorisé dans les commentaires/chunks
        strip=True         # supprimer tout balisage non autorisé
    )

# Usage :
comment.content = sanitize_input(request.form["content"])
chunk.name = sanitize_input(request.form["chunk_name"])
```

### 10.4 Authentification & Sessions

```python
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ─── Hashing des mots de passe (bcrypt/scrypt) ───
password_hash = generate_password_hash(password, method='scrypt')  # ← plus sûr que pbkdf2

# Vérification
user = User.query.filter_by(prenom=prenom, nom=nom).first()
if user and check_password_hash(user.password_hash, submitted_password):
    session['user_id'] = user.id

# ─── Decorateur login_required (sûr) ───
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('connexion'))
        return f(*args, **kwargs)
    return decorated_function

# Usage :
@login_required
def upload_chunk():
    ...
```

### 10.5 Protection des inputs utilisateurs (tous les formulaires)

**Validation stricte côté serveur — ne jamais faire confiance aux données client :**

```python
from wtforms import Form, StringField, PasswordField, URLField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

# ─── Formulaire de connexion (prénom + nom) ───
class LoginForm(Form):
    prenom = StringField('Prénom', validators=[DataRequired(), Length(1, 100)])
    nom = StringField('Nom', validators=[DataRequired(), Length(1, 100)])
    password = PasswordField('Mot de passe', validators=[DataRequired()])

# ─── Formulaire d'inscription ───
class RegisterForm(Form):
    prenom = StringField('Prénom', validators=[DataRequired(), Length(1, 100), Regexp(r'^[a-zA-Zéèêëçàùû]+$')])
    nom = StringField('Nom', validators=[DataRequired(), Length(1, 100), Regexp(r'^[a-zA-Zéèêëçàùû]+$')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(8)])

# ─── Formulaire d'upload chunk ───
class ChunkUploadForm(Form):
    chunk_name = StringField('Nom du fragment', validators=[DataRequired(), Length(1, 200), Regexp(r'^[a-zA-Z0-9\-_éèêëçàùû ]+$')])
    parent_item_id = IntegerField('Item parent', validators=[Optional()])
```

**Règles de validation :**
| Champ | Règle | Pourquoi |
|-------|-------|----------|
| `prenom` / `nom` | `[a-zA-Zéèêëçàùû]` max 100 | Bloquer les caractères spéciaux, length overflow |
| `email` | validation email stricte | Format standard RFC 5322 |
| `password` | min 8 caractères | Sécurité basique |
| `chunk_name` | `[a-zA-Z0-9\-_ ]` max 200 | Pas de `/` ni `\` (path traversal) |
| `url` (viz_link) | validation regex URL stricte | Bloquer `javascript:`, `data:`, etc. |

### 10.6 Path Traversal (prévention des attaques de fichiers)

**Pour les uploads de chunks :**

```python
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv', 'shp', 'geojson', 'gpkg', 'json', 'xml'}

def is_allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─── Stockage sécurisé ───
@app.route("/api/upload/chunk", methods=["POST"])
@login_required
def upload_chunk():
    file = request.files["file"]

    if not is_allowed_file(file.filename):
        return jsonify({"error": "Format non autorisé"}), 400

    # secure_filename() supprime les `../` et caractères dangereux
    safe_name = secure_filename(file.filename)

    # Ne JAMAIS utiliser le nom brut dans un chemin
    upload_path = os.path.join('/uploads', str(current_user.id), safe_name)
    file.save(upload_path)

    # ...
```

### 10.7 Protection des URLs de visualisation (XSS via `javascript:` / `data:`)

**Validation stricte des URLs externes :**

```python
import re
from urllib.parse import urlparse

def validate_external_url(url: str) -> bool:
    """Vérifier qu'une URL est sûre pour le lien de visualisation."""
    try:
        parsed = urlparse(url)
        # Bloquer javascript:, data:, vbscript:, et les URLs relatives sans protocole
        if parsed.scheme not in ('http', 'https'):
            return False
        # Bloquer l'authentification via URL pour éviter le phishing
        if '@' in url:
            return False
        return True
    except Exception:
        return False

# Usage :
link.url = request.form["url"]
if not validate_external_url(link.url):
    abort(400, "URL invalide")
```

### 10.8 Rate Limiting (protection contre brute-force sur le login)

```python
# requirements.txt — ajouter :
# Flask-Limiter>=3.0

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["20 per day", "5 per hour"]
)

@limiter.limit("5 per hour")  # 5 tentatives de connexion par heure/IP
@app.route("/connexion", methods=["POST"])
def connexion_post():
    ...
```

### 10.9 Headers HTTP de sécurité — DÉJÀ CONFIGURÉS ✅

Vérifier que ces headers existent dans `app.py` (déjà présent, ligne ~302-314) :

```python
@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"           # Bloquer clickjacking
    response.headers["X-Content-Type-Options"] = "nosniff"  # Bloquer MIME sniffing
    response.headers["X-XSS-Protection"] = "1; mode=block"  # XSS filter navigateur
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # HTTPS forcé (ajouter)
    response.headers["Content-Security-Policy"] = (...)      # CSP déjà configuré
    return response
```

### 10.10 Protection de la base de données

**Principes :**
- **Toujours utiliser SQLAlchemy ORM** — jamais de requête SQL brute avec f-string
- **Utiliser des transactions explicites** pour éviter les partial writes :
```python
try:
    chunk = DataChunk(...)
    upload = UserUpload(...)
    db.session.add(chunk)
    db.session.add(upload)
    db.session.commit()           # ← tout ou rien
except Exception as e:
    db.session.rollback()         # ← annuler si erreur
    app.logger.error(f"DB error: {e}")
```

- **Vérifier les permissions des fichiers de l'app :**
```bash
chmod 600 .secret        # clé secrète Flask
chmod 750 .env           # variables d'environnement (incluent DB password)
chown root:appuser .secret
chown appuser:appgroup .env
```

- **Variables sensibles dans `.env` et `docker-compose.yml` — jamais en dur :**
```yaml
# docker-compose.yml ❌ NE JAMAIS FAIRE ÇA :
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_PASSWORD: "mon_mot_de_passe_en_dans_le_code"  # ← VULNÉRABLE
```

**Ce qui est protégé et ce qui ne l'est pas :**

| Menace | Protégé par | Statut dans le projet |
|--------|-------------|----------------------|
| Injections SQL | SQLAlchemy ORM (parameterized) | ✅ Garanti |
| CSRF | Flask-WTF CSRFProtect | ✅ Déjà actif |
| XSS | Jinja2 auto-escape + bleach | ⚠️ Ajouter bleach pour les inputs |
| Path traversal | `secure_filename()` | ❌ À implémenter dans upload |
| URL injection | Validation stricte regex | ❌ À implémenter |
| Brute-force | Flask-Limiter | ❌ À ajouter |
| Session hijacking | HttpOnly cookies + CSRF token | ✅ Déjà configuré |
| SQL brute force (login) | Hashing scrypt/bcrypt | ✅ `generate_password_hash` |
