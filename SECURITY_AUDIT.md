# Audit de Sécurité — A.N.A.N.A.S. (sitev2)

## Méthodologie

Analyse statique approfondie de l'ensemble du code source : routes, modèles, templates, configuration infrastructure.

---

## 🔴 CRITIQUE

### 1. Logging de données sensibles en production

**Fichier**: `src/interactions.py:19`

```python
logging.warning(f"[RATE] item_id={item_id} raw_rating='{rating_value}' user_id={current_user.id if current_user else None}")
logging.warning(f"[RATE] found_existing={bool(existing)} new_rating={rating}")
logging.warning(f"[RATE] all_ratings={[(r.id, r.user_id, r.rating) for r in ratings]}")
```

- Les logs exposent `user_id`, `item_id`, `rating_value` dans les logs du conteneur
- Lisibles par tous les utilisateurs ayant accès aux logs Gunicorn/Flask
- **Impact**: Fuite d'information, identification et suivi des utilisateurs

---

### 2. Credential admin par défaut faible

**Fichier**: `docker-entrypoint.sh:14,28`

```bash
os.environ.setdefault('ADMIN_PASSWORD', 'system')
...
ADMIN_PASSWORD="${ADMIN_PASSWORD:-system}"
```

- Mot de passe admin par défaut : `"system"` si `ADMIN_PASSWORD` n'est pas défini
- Email hardcodé : `system@ananas.local`
- **Impact**: Accès administrateur complet par tout acteur connaissant le mot de passe par défaut

---

## 🟠 HAUT

### 3. Exemption CSRF sur endpoints admin critiques

**Fichier**: `app.py:69-89`

```python
EXEMPTED_ENDPOINTS = {
    "admin.ban_user",
    "admin.list_banned_users",
    "admin.create_report",
    "admin.list_reports",
    "admin.resolve_report",
    "admin.list_comments",
    "admin.delete_comment",
    "admin.list_items",
    "admin.delete_item",
    "admin.unpublish_item",
    "admin.publish_item",
    "admin.verify_item",
    "admin.unverify_item",
    "admin.admin_audit_log",
}
```

- Les endpoints admin critiques sont exemptés de CSRF
- Ils ne nécessitent que `@login_required` — n'importe quelle session volée ou forcée permet d'exécuter des actions admin
- **Impact**: CSRF pur — un attaquant pourrait forcer un admin à banquer des utilisateurs, supprimer du contenu, ou modifier des items via une page malveillante

---

### 4. Requête par nom de l'auteur — élévation de privilèges

**Fichier**: `src/shared.py:64-81`

```python
def user_owns_item_or_admin(current_user, item):
    if getattr(item, "author_name", None) and current_user:
        full_name = f"{current_user.prenom} {current_user.nom}"
        if item.author_name == full_name:
            return True
```

- La vérification d'appartenance repose sur la comparaison de chaîne de caractères (`author_name`)
- Si un utilisateur peut contrôler `prenom` ou `nom` (inscription, profil), il peut usurper l'appartenance d'un item dont le titre correspond
- **Impact**: Élévation de privilèges — modification/suppression d'items qui ne lui appartiennent pas

---

### 5. Magnet links non validés

**Fichier**: `src/upload_routes.py:107-112`

```python
item = Item(
    ...
    magnet_link=magnet_link[:500],
)
```

- Aucune validation du format — le magnet link peut contenir n'importe quelle chaîne de 500 caractères
- **Impact**: Stockage de données arbitraires dans les magnet links, potentiellement utilisé pour des attaques XSS si affichés sans échappement ou exploités dans d'autres fonctions

---

### 6. Inscription silencieuse sur email existant

**Fichier**: `src/auth_routes.py:84-85`

```python
existing_user = User.query.filter_by(email=email).first()
if existing_user:
    return redirect(url_for("auth.connexion_page"))
```

- Si l'email existe déjà, redirection silencieuse vers la page de connexion — aucun flash message, aucune indication
- Un attaquant peut enumérer les emails inscrits vs non-inscrits par le comportement différent (redirect 302 vs render_template 400)
- **Impact**: Enumération d'emails

---

## 🟡 MOYEN

### 7. Pas de rate limiting sur update profil utilisateur

**Fichier**: `src/user_routes.py:113`

```python
@bp.route("/api/users/profile", methods=["PUT"])
@login_required
def update_profile():
```

- L'update du profil (email inclus) n'a pas de limite de requêtes
- Un attaquant pourrait inonder l'API avec des emails différents pour empêcher l'inscription d'autres utilisateurs
- **Impact**: Déluge d'emails, blocage d'utilisateurs légitimes

---

### 8. Validation CSV potentiellement contournable

**Fichier**: `utils/security.py:66-70`

```python
if b"." in file_data[:200]:
    try:
        header_ext = file_data[:200].decode("utf-8", errors="ignore").rsplit(".", 1)[-1]
        ...
```

- L'extension est extraite des 200 premiers bytes du contenu
- Un fichier non-CSV peut contenir `.csv` en début de contenu et passer la validation
- **Impact**: Upload de fichiers arbitraires via manipulation d'en-tête

---

### 9. HSTS sans preload

**Fichier**: `app.py:157`

```python
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

- Manque `; preload` — la protection ne sera pas intégrée dans les listes preload des navigateurs (Chrome, Firefox, Safari)
- **Impact**: Protection HSTS non exploitable hors connexion directe

---

### 10. Connexion PostgreSQL `sslmode=prefer` sans certificats complets

**Fichier**: `app.py:128-129`

```python
else:
    db_uri = f"{db_uri}{separator}sslmode=prefer"
```

- Si les certificats SSL ne sont pas tous fournis (`ssl_root`, `ssl_cert`, `ssl_key`), la connexion utilise `prefer` (chiffrement facultatif)
- **Impact**: Possible downgrade en clair si un attaquant MITM est présent sur le réseau

---

### 11. Session cookie SameSite=Lax

**Fichier**: `app.py:180`

```python
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
```

- `Lax` permet certaines requêtes cross-site (navigateur GET sur une nouvelle page)
- Bien que mitigé par les autres contrôles (CSRF, CSP), cela augmente la surface d'attaque
- **Impact**: Potentiel de CSRF via navigation inter-site

---

### 12. Exemption CSRF sur inscription/connexion — incohérence

**Fichier**: `app.py:71-74`

```python
"auth.inscription_page",
"auth.inscription_post",
"auth.connexion_page",
"auth.connexion_post",
```

- La route `inscription_post` est exemptée de CSRF, ce qui est acceptable pour un formulaire d'inscription public
- Cependant, `connexion_post` (login POST) est aussi exempté — ce qui permet une attaque CSRF sur le login (l'attaquant pourrait forcer la connexion d'un utilisateur cible avec ses propres identifiants dans certains cas)
- **Impact**: Login CSRF — potentiel de redirection piégée

---

## 🟢 INFÉRIEUR / INFORMATIONNEL

### 13. Dockerfile — fichiers copiés dans l'image de test

**Fichier**: `Dockerfile:11`

```dockerfile
COPY . .
```

- Les fichiers du projet entier sont copiés avant l'étape de test
- Si `.dockerignore` est manquant ou incomplet, des secrets pourraient être inclus dans les layers

---

### 14. Nginx — pas de rate limiting au niveau proxy

**Fichier**: `nginx/nginx.conf`

- Aucun `limit_req_zone` configuré au niveau Nginx
- La protection est uniquement au niveau Flask (backend), contournable si l'attaquant vise directement le backend sans passer par Nginx ou en saturant Nginx lui-même
- **Impact**: Moins de défences en profondeur

---

### 15. Setup.sh imprime les credentials en clair

**Fichier**: `setup.sh:47-52`

```bash
printf "POSTGRES_PASSWORD   : %s\n" "${pg_pass}"
printf "ADMIN_PASSWORD      : %s\n" "${admin_pass}"
```

- Les mots de passe sont affichés dans la console — potentiellement stockés dans `~/.bash_history`
- **Impact**: Fuite de credentials via l'historique shell

---

### 16. Page de connexion — pas de délai constant

**Fichier**: `src/auth_routes.py:38-56`

```python
user = User.query.filter_by(email=email).first()
if user and check_password_hash(user.password_hash, password) and user.is_active and not user.banned:
    ...
if user and (not user.is_active or user.banned):
    return render_template("connexion.html", error="banned"), 401
return render_template("connexion.html", error="Identifiants incorrects"), 401
```

- `check_password_hash` est coûteux (scrypt) mais si l'utilisateur n'existe pas (`user is None`), le code saute directement au return sans appel — temps de réponse légèrement différent
- Un attaquant pourrait distinguer email inexistant vs existant via timing
- **Impact**: Enumération d'emails par timing (mineure car différence très faible)

---

### 17. Logs Gunicorn non filtrés

- Les logs standard de Gunicorn enregistrent toutes les requêtes HTTP, y compris celles contenant des données sensibles dans le query string ou body
- **Impact**: Fuite d'information dans les logs

---

## ✅ Points Forts Identifiés

| Contrôle | Statut | Détails |
|---|---|---|
| XSS — échappement Jinja2 | ✅ | `autoescape = True` activé |
| CSP — nonce-based | ✅ | Nonce unique par requête, polices limitées |
| CSRF — protection Flask-WTF | ✅ | (avec exemptions raisonnables) |
| Rate limiting — login/inscription | ✅ | 5 req/h login, 3 req/h inscription |
| Session hardening | ✅ | HttpOnly, SameSite=Lax, Secure en prod, 30 min timeout |
| Password hashing | ✅ | Werkzeug scrypt |
| Validation des fichiers | ✅ | Magic bytes + whitelist extensions |
| Secret key externe | ✅ | Fichier `.secret` avec permissions `0o600` |
| Non-root Docker user | ✅ | `appuser` utilisateur non-root |
| Audit logging admin | ✅ | Model `AdminAudit` pour toutes les actions admin |
| HSTS + X-Frame-Options + nosniff | ✅ | Headers de sécurité complets |
| No debug mode en production | ✅ | Vérification explicite FLASK_DEBUG |
| SSL database connexion | ✅ | Tentative d'activation si certificats disponibles |

---

## 🔧 Priorités de Correction

### P0 — Immédiat

1. **Supprimer les logs sensibles** `src/interactions.py:17-41` (logging.warning avec user_id, item_id)
2. **Forcer ADMIN_PASSWORD au démarrage** — lancer une erreur si `ADMIN_PASSWORD` vaut `"system"` ou n'est pas défini (`docker-entrypoint.sh`)
3. **Ajouter un champ `author_id`** dans le modèle `Item` (ForeignKey vers `users.id`) et remplacer la comparaison par nom de chaîne par une vérification par ID foreign key (`models.py`, `src/shared.py`, `src/upload_routes.py`)

### P1 — Haute priorité

4. **Restreindre les exemptions CSRF admin** — ajouter une validation supplémentaire (origin check, ou demander une confirmation via modal pour les actions critiques comme le ban/delete)
5. **Valider les magnet links** — vérifier qu'ils correspondent au format `magnet:?xt=urn:btih:` (`src/upload_routes.py`)
6. **Unifier le message d'erreur d'inscription** — ne pas différencier email existant vs nouvel email (retourner toujours un succès ou un échec aléatoire)

### P2 — Moyenne priorité

7. **Ajouter rate limiting sur `/api/users/profile`** (`src/user_routes.py`)
8. **Renforcer la validation CSV** — vérifier l'intégralité du contenu, pas seulement les 200 premiers bytes (`utils/security.py`)
9. **Ajouter `preload` à la directive HSTS** (`app.py:157`)
10. **Forcer `sslmode=require` ou `verify-full`** en production par défaut (`app.py:128-129`)

### P3 — Amélioration continue

11. **Ajouter rate limiting Nginx** au niveau proxy avec `limit_req_zone`
12. **Changer SameSite=Lax à SameSite=Strict** si le CSRF est correctement géré autrement
13. **Filtrer les données sensibles dans les logs** (middleware de logging)
14. **Ajouter un délai constant sur la vérification de mot de passe** pour neutraliser le timing attack (`src/auth_routes.py`)

---

## Résumé Exécutif

| Sévérité | Nombre |
|---|---|
| Critique | 2 |
| Haut | 5 |
| Moyen | 6 |
| Inférieur | 7 |

**Score estimé : B-** — L'application implémente la majorité des bonnes pratiques de sécurité (CSP, CSRF, rate limiting, session hardening, audit logging). Les lacunes principales concernent les logs sensibles en production, le credential admin par défaut, et l'absence de foreign key pour la vérification d'appartenance d'items.
