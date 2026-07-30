# Rapport d'Audit de Sécurité — A.N.A.N.A.S (sitev2)

**Date :** 30 juillet 2026  
**Cible :** `/home/ssd/Documents/memoire_main/sitev2`  
**Technologies :** Flask 3.1.0, PostgreSQL 18, Docker, Nginx, qBittorrent

---

## Résumé

| Sévérité | Nombre | Description |
|----------|--------|-------------|
| **CRITIQUE** | 3 | Fuite de credentials, SSRF, CSRF affaibli |
| **HAUTE** | 6 | qBittorrent par défaut, mode dev, upload sans vérification MIME, sessions persistantes, SQL brut |
| **MOYENNE** | 7 | CORS, permissions, CSP, validation entrées |
| **BASSE** | 5 | Headers, CDN, autoindex, volume secret |

---

## CRITIQUE

### C1 — Credentials en dur dans le dépôt (`.env`)

- **Fichier :** `.env:1-12`
- **Code :**
  ```env
  POSTGRES_PASSWORD=8b9bde6d...
  ADMIN_PASSWORD=ZEqNEYqE...
  FLASK_SECRET_KEY=70999fc7...
  SQLALCHEMY_DATABASE_URI=postgresql://...
  ```
- **Risque :** Le fichier `.env` contenant les credentials de la base de données, le mot de passe admin et la clé secrète Flask est tracé dans git. Toute personne avec accès au dépôt peut compromettre la base, forger des sessions et obtenir un accès admin.
- **Correctif :** Ajouter `.env` au `.gitignore`, **faire la rotation immédiate de tous les credentials**, utiliser des variables d'environnement ou un gestionnaire de secrets.

### C2 — SSRF via la fonctionnalité de réplication admin

- **Fichier :** `src/admin/replication.py:17,51,155`
- **Code :**
  ```python
  remote_url = (data.get("url") or "").strip().rstrip("/")
  json_url = f"{remote_url}/catalogue/{cat_type}/{page}/json"
  with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
  ```
- **Risque :** Un admin peut faire fetch le serveur vers des URLs arbitraires. `urllib` suit les redirections et peut accéder à des services internes (`http://localhost:5001`, `http://postgres:5432`, etc.). SSRF vers le réseau interne.
- **Correctif :** Valider l'URL contre une liste de domaines autorisés, restreindre les redirections vers les IP privées, ou utiliser `requests` avec un blocage des plages RFC 1918.

### C3 — Token CSRF accessible en JavaScript (cookie non-HttpOnly)

- **Fichier :** `app.py:211-218`, `static/js/csrf.js:6-16`
- **Code :**
  ```python
  response.set_cookie("csrf_token", csrf_signed, httponly=False, ...)
  ```
  ```javascript
  function getCsrfToken() {
    var name = 'csrf_token=';
    var cookies = document.cookie.split(';');
  ```
- **Risque :** Le token CSRF est accessible en JavaScript car `httponly=False`. Le pattern Double Submit Cookie perd son intérêt si le cookie est lisible par le JS. Une XSS (même partielle) permettrait de voler le token et forger des requêtes.
- **Correctif :** Passer le token CSRF via une balise `<meta>` ou un champ caché. Mettre `httponly=True` sur le cookie CSRF.

---

## HAUTE

### H1 — Credentials qBittorrent par défaut

- **Fichier :** `docker-compose.yml:33`, `src/image_cache.py:15-17`, `docker-entrypoint.sh:71,81`
- **Code :**
  ```yaml
  QBITTORRENT_PASSWORD=${QBITTORRENT_PASSWORD-adminadmin}
  ```
- **Risque :** Le mot de passe par défaut `adminadmin` est utilisé si non surchargé. Un attaquant avec accès réseau au port 8081 (Web UI qBittorrent) peut contrôler les téléchargements torrent.
- **Correctif :** Générer un mot de passe aléatoire fort dans `setup.sh` et le passer systématiquement. Supprimer la valeur par défaut.

### H2 — `FLASK_ENV=development` dans Docker

- **Fichier :** `docker-compose.yml:30`
- **Code :** `- FLASK_ENV=development`
- **Risque :** Le mode développement peut activer le debugger Flask. En cas d'erreur, le debugger interactif pourrait être exposé, menant à de l'exécution de code à distance.
- **Correctif :** Remplacer par `FLASK_ENV=production`. L'app le gère déjà (`app.py:65-71`), mais le décalage est risqué.

### H3 — Aucune validation MIME sur l'upload d'avatar

- **Fichier :** `src/user_routes.py:84-100`
- **Code :**
  ```python
  ext = os.path.splitext(file.filename)[1].lower()
  if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
  file.save(filepath)
  ```
- **Risque :** Seule l'extension est vérifiée, pas le contenu réel. Un fichier malveillant renommé en `.png` peut être uploadé.
- **Correctif :** Valider le type MIME avec `python-magic` ou `PIL.Image`. Servir les avatars avec `X-Content-Type-Options: nosniff`.

### H4 — Session non invalidée après bannissement/changement de mot de passe

- **Fichier :** `src/admin/users.py:42-47`, `src/user_routes.py:75`
- **Code :**
  ```python
  user.banned = True
  user.is_active = False
  db.session.commit()  # La session existe toujours
  ```
- **Risque :** Un utilisateur banni conserve sa session active jusqu'à expiration (30 min). Il peut continuer à utiliser l'application.
- **Correctif :** Invalider les sessions lors du bannissement et du changement de mot de passe (champ `session_version` en base).

### H5 — SQL brut (`ALTER TABLE`) dans le chemin de production

- **Fichier :** `app.py:52-55`
- **Code :** `db.session.execute(db.text("ALTER TABLE items ADD COLUMN ..."))`
- **Risque :** Anti-patron dangereux. L'utilisation de SQL brut dans le code applicatif plutôt que dans les migrations Alembic peut mener à des injections si jamais ces chaînes deviennent paramétrées.
- **Correctif :** Utiliser exclusivement Alembic pour les migrations de schéma.

### H6 — Absence de rate limiting sur le changement de mot de passe

- **Fichier :** `src/user_routes.py:58-77`
- **Code :** Aucun décorateur `@limiter.limit()` sur `change_password()`
- **Risque :** Un attaquant peut bruteforcer le mot de passe actuel pour détourner un compte. La page de login est limitée (5/h), mais pas le changement de mot de passe.
- **Correctif :** Ajouter `@limiter.limit("5 per hour")` sur la route `change_password`.

---

## MOYENNE

### M1 — Absence de configuration CORS explicite

- **Fichier :** `app.py`
- **Risque :** Aucun header CORS n'est défini. L'application suppose une origine unique. Si un accès cross-origin est nécessaire un jour, tout sera bloqué.
- **Correctif :** Ajouter une configuration CORS explicite (même si c'est `same-origin` par défaut).

### M2 — Message d'erreur trompeur sur la suppression d'organisation

- **Fichier :** `src/organization_routes.py:406-421`
- **Code :** Le commentaire dit "Seul le propriétaire peut supprimer", mais le code vérifie `delete_org` (custom role).
- **Risque :** Confusion entre le code et le comportement attendu. Un membre avec le rôle `delete_org` peut supprimer l'organisation sans en être propriétaire.
- **Correctif :** Aligner le message avec la vérification réelle, ou restreindre aux propriétaires uniquement.

### M3 — CSP manque `upgrade-insecure-requests`

- **Fichier :** `app.py:196-206`
- **Risque :** Si une page charge des ressources HTTP (images, scripts), elles peuvent être interceptées (MITM).
- **Correctif :** Ajouter `upgrade-insecure-requests` à l'en-tête CSP.

### M4 — Pas de vérification `request.is_json` dans les routes admin

- **Fichier :** Routes admin (ex: `src/admin/users.py:21`)
- **Code :** `data = request.get_json(silent=True) or {}` sans vérifier `request.is_json`
- **Risque :** Des requêtes form-encodées sont silencieusement ignorées, menant à des comportements inattendus.
- **Correctif :** Vérifier `request.is_json` et retourner 415 si absent.

### M5 — Extension non sécurisée dans le chemin de l'avatar

- **Fichier :** `src/user_routes.py:98`
- **Code :** `filename = f"avatar_{current_user.id}_{secrets.token_hex(8)}{ext}"`
- **Risque :** L'extension `ext` vient du fichier uploadé. Si elle contient `../../`, il y a un risque limité de path traversal.
- **Correctif :** Valider l'extension contre une whitelist avant la construction du chemin. Utiliser `werkzeug.utils.secure_filename()`.

### M6 — Pas de vérification d'email lors de l'inscription

- **Fichier :** `src/auth_routes.py:53-83`
- **Risque :** N'importe qui peut s'inscrire avec n'importe quelle adresse email sans prouver sa possession. Permet les comptes spam et les abus.
- **Correctif :** Implémenter un flux de vérification d'email avant l'activation du compte.

---

## BASSE

### L1 — `unpkg.com` autorisé dans la CSP

- **Fichier :** `app.py:198-199`
- **Code :** `script-src 'self' 'nonce-{nonce}' https://unpkg.com;`
- **Risque :** `unpkg.com` est un CDN qui sert n'importe quel package npm. Un compromission du CDN permettrait de servir des scripts malveillants.
- **Correctif :** Supprimer `unpkg.com` de la CSP ou utiliser des SRI hashes.

### L2 — Autoindex non explicitement désactivé dans Nginx

- **Fichier :** `nginx/nginx.conf:42`
- **Risque :** `autoindex` est `off` par défaut, mais non explicite.
- **Correctif :** Ajouter `autoindex off;` explicitement.

### L3 — Fichier `.secret` persistant dans un volume Docker

- **Fichier :** `docker-compose.yml:40`
- **Risque :** Le volume `secret_key` persiste la clé secrète à travers les rebuilds.
- **Correctif :** Utiliser les variables d'environnement exclusivement pour les secrets.

---

## Recommandations Prioritaires

1. **Immédiat :** Retirer `.env` du suivi git et faire la rotation de tous les credentials (C1)
2. **Immédiat :** Restreindre les URLs dans `replication.py` pour empêcher le SSRF (C2)
3. **Haute :** Rendre le cookie CSRF `httponly=True` et utiliser une balise `<meta>` (C3)
4. **Haute :** Changer `FLASK_ENV=development` en `production` dans `docker-compose.yml` (H2)
5. **Haute :** Ajouter la validation MIME sur les uploads d'avatar (H3)
6. **Haute :** Invalider les sessions au bannissement (H4)
7. **Haute :** Supprimer le mot de passe par défaut `adminadmin` de qBittorrent (H1)

---

*Audit réalisé le 30 juillet 2026. Ce document doit être mis à jour après chaque modification majeure de l'application.*