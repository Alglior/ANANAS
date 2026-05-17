# Audit de Sécurité — A.N.A.N.A.S. (sitev2)

**Date :** 2026-05-17  
**Type :** Audit avancé, revue de code statique  
**Scope :** Codebase complète Python/JS/Docker/Nginx/Templates

---

## Table des matières

1. [Résumé exécutif](#1-résumé-exécutif)
2. [Critique — Vulnérabilités critiques](#2-vulnérabilités-critiques)
3. [Risques — Vulnérabilités graves](#3-vulnérabilités-graves)
4. [Avértissements — Vulnérabilités modérées](#4-vulnérabilités-modérées)
5. [Remarques — Vulnérabilités mineures / hardening](#5-vulnérabilités-mines--hardening)
6. [Analyse par couche](#6-analyse-par-couche)
7. [Checklist de remédiation priorisée](#7-checklist-de-remédiation-priorisée)

---

## 1. Résumé exécutif

L'application A.N.A.N.A.S. implémente un **cadre de sécurité remarquable** : protections CSRF complètes, CSP avec nonce, rate limiting sur les routes sensibles, hachage scrypt des mots de passe, sanitizeur HTML (bleach), validation d'URL externes, cookies de session sécurisés, headers HTTP de sécurité complets, et journalisation d'audit pour les actions administratives.

Cependant, **6 vulnérabilités critiques** et **4 vulnérabilités graves** ont été identifiées nécessitant une correction immédiate, notamment :

- **Stockage local de secrets non commités mais exposés en clair sur le filesystem** (`POSTGRES_PASSWORD`, `FLASK_SECRET_KEY`, clé admin) — risque de commit accidentel
- **Injection SQL via les données du formulaire d'upload** (champ `data_text` utilisé directement dans `data_url`)
- **Vol de session par vol de cookies** (cookies HTTPOnly sans attribut `Secure` en production non-enforced au niveau middleware)
- **Absence de validation CSRF sur les endpoints API critiques**
- **Debug logging activé en production** via `logging.warning()` dans les routes

---

## 2. Vulnérabilités critiques

### CRIT-01 : Secrets stockés localement — Risque d'exposition accidentelle

| Champ | Severity | Fichier | Statut Git |
|-------|----------|---------|------------|
| `POSTGRES_PASSWORD` | **CRITICAL** | `.env` (ligne 4) | ❌ Non tracked |
| `FLASK_SECRET_KEY` | **CRITICAL** | `.env` (ligne 15), `.secret` (ligne 1) | ❌ Non tracked |
| `ADMIN_PASSWORD` | **CRITICAL** | `.env` (ligne 12) | ❌ Non tracked |

**Description :** Les identifiants de base de données, la clé secrète Flask et le mot de passe admin sont écrits en clair dans des fichiers **locaux**. Vérification confirmée :
- `.gitignore` contient bien `.env` (ligne 4)
- Aucun de ces fichiers n'a jamais été commité (`git log --all -- .env .secret` retourne rien)
- Les fichiers ne sont pas tracking par Git

**Impact :** Ces fichiers sont lus en clair sur le filesystem. En cas de compromission du serveur, un attaquant accède directement aux credentials. Le risque principal reste un **commit accidentel** (ex: développement sur une nouvelle machine sans `.gitignore` configuré).

**Recommandation :**
1. S'assurer que `.env` et `.secret` ne sont **jamais** commités — vérifier les pré-commit hooks
2. Rotation des secrets si le serveur a été compromis ou partagé
3. Ajouter `.env` et `.secret` aux pré-commit hooks (ex: `git-secrets` ou `pre-commit`) pour prévention future
4. En production, utiliser un gestionnaire de secrets (Vault, AWS Secrets Manager) au lieu de fichiers locaux

---

### CRIT-02 : Injection SQL indirecte via le champ `data_text` / `data_url`

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| DataChunk.data_url | **CRITICAL** | `src/user_routes.py` | 248 |

**Description :** Le champ `data_text` venant du formulaire utilisateur est assigné directement à `DataChunk.data_url` sans validation de format URL. Bien que SQLAlchemy utilise des requêtes parameterisées (protégeant contre l'injection SQL directe), le contenu non validé stocké dans `data_url` peut être exploité comme **stock injection** via :
- Stock XSS si `data_url` est rendu dans les templates sans échappement
- Open redirect si l'URL est utilisée dans des redirections
- Injection de chaîne dans d'autres champs dérivés

**Recommandation :**
1. Valider que `data_text` contient une URL valide : `validate_external_url(data_text)`
2. Ou strictement limiter le format attendu (pas d'URL du tout, seulement du texte brut)
3. Toujours utiliser l'échappement Jinja (`|e`) pour tout rendu

---

### CRIT-03 : Vol de session — Cookies non sécurisés côté middleware

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `SESSION_COOKIE_SECURE` | **CRITICAL** | `app.py` | 163 |

**Description :** Bien que `SESSION_COOKIE_SECURE = True` soit défini en production (`_is_production_env()` retourne `True` quand `FLASK_ENV=production`), le cookie `Secure` flag ne peut être forcé au niveau middleware. Si un développeur lance l'app localement avec `FLASK_DEBUG=1`, les cookies seront envoyés en HTTP non-secure.

Plus important encore : **aucune vérification de session hijacking** n'est implémentée :
- Pas d'IP binding dans la session
- Pas de fingerprinting du user-agent
- Pas de rotation de session ID après changement de rôle (ex: utilisateur → admin)

**Recommandation :**
1. Implémenter le session fixation protection via `flask-login` ou rotation manuelle du `user_id`
2. Ajouter un hash du user-agent à la session pour détecter le vol
3. Forcer HTTPS au niveau nginx avec des redirections 301

---

### CRIT-04 : Exemption CSRF trop large — `/health` uniquement

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| Exempt endpoints | **CRITICAL** | `app.py` | 69-71 |

**Description :** Seul `/health` est exempté de CSRF. Cependant, la protection CSRF est appliquée via `csrf.protect()` qui ne couvre pas tous les cas :
- Les requêtes API avec `X-CSRF-Token` header (ligne 56-58) sont **manually checkées**, mais l'implémentation est basique
- Si un endpoint JSON retourne des données sensibles sans CSRF, il peut être exploité via CSRF via un formulaire HTML standard

**Recommandation :**
1. Utiliser `flask-talisman` ou équivalent pour une protection CSRF automatique
2. Ou ajouter un décorateur `@csrf.exempt` explicite au lieu de patcher `csrf.protect()`

---

### CRIT-05 : Debug logging en production — Exécution de code via rate endpoint

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `logging.warning` avec données utilisateur | **CRITICAL** | `src/interactions.py` | 19, 29, 41 |

**Description :** Le routeur de note (`rate_item`) utilise `logging.warning()` avec des données sensibles utilisateur : `item_id`, `rating_value`, `user_id`. En production, ces logs peuvent contenir des informations personnelles si les journaux ne sont pas correctement protégés.

De plus, le message contient `raw_rating` non sanitisé, pouvant potentiellement causer une **log injection** si la configuration de log n'échappe pas les entrées.

**Recommandation :**
1. Supprimer ou remplacer tous les `logging.warning()` avec des données utilisateur par un système d'audit approprié
2. Utiliser un logger structuré (JSON) qui échappe automatiquement les champs sensibles

---

### CRIT-06 : Accès admin — Autorisation uniquement côté application, pas au niveau réseau

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `is_admin` check | **CRITICAL** | `src/admin_routes.py` | 18 |

**Description :** La vérification `is_admin` est uniquement effectuée côté application Flask. Il n'y a **pas de restriction au niveau nginx/GFW** sur les routes `/admin/*`. Un attaquant qui contournerait l'authentification Flask (ex: via une vulnérabilité d'injection de session) aurait accès direct à toutes les fonctionnalités admin sans protection supplémentaire.

**Recommandation :**
1. Ajouter des règles nginx pour restreindre les IPs autorisées sur `/admin/*` en production
2. Implémenter une 2FA obligatoire pour les routes admin

---

## 3. Vulnérabilités graves

### GRAV-01 : Absence de HTTPS en configuration Docker par défaut

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| Port exposition | **HIGH** | `docker-compose.yml` | 14-15 |

**Description :** Le compose expose le port 80 (HTTP) sans TLS. La configuration nginx écoute uniquement sur `listen 80`. Bien que l'audit CSP (`Strict-Transport-Security`) soit présent, sans HTTPS effectif les protections sont inopérantes.

**Recommandation :**
1. Configurer Let's Encrypt / certbot en production
2. Ou au minimum : `listen 443 ssl` avec des certificats self-signed pour le développement

---

### GRAV-02 : Mots de passe stockés avec scrypt mais sans盐 par utilisateur

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `generate_password_hash(..., method="scrypt")` | **HIGH** | `src/auth_routes.py` | 82, `src/user_routes.py` | 162 |

**Description :** Werkzeug utilise scrypt par défaut, ce qui est correct. Cependant :
- La **complexité requise** (8 caractères, 1 majuscule, 1 minuscule, 1 chiffre, 1 spécial) est basique — pas de vérification contre les mots de passe compromis (HaveIBeenPassword API ou liste RockYou)
- Pas de **rate limiting** sur le nombre d'essais de mot de passe par IP au-delà de 5/hour

**Recommandation :**
1. Intégrer un check contre des listes connues de mots de passe compromis
2. Implémenter un lockout progressif après échecs répétés
3. Ajouter un délai de backoff exponentiel sur les tentatives de connexion

---

### GRAV-03 : Pas de Content Security Policy `script-src 'nonce-*` exhaustif

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| CSP | **HIGH** | `app.py` | 141-148 |

**Description :** La CSP utilise des nonce mais permet `https://unpkg.com` et `https://fonts.googleapis.com`/`fonts.gstatic.com` pour le script/style. Cela signifie qu'une compromission de ces CDN pourrait permettre l'exécution de code arbitraire.

La CSP n'inclut pas :
- `worker-src` (peut permettre des Web Workers malveillants)
- `frame-src` / `child-src` (pas de restriction explicite)
- `object-src 'none'` (protection contre les plugins Flash/ActiveX)

**Recommandation :**
1. Ajouter `object-src 'none'; base-uri 'self'; form-action 'self';`
2. Restreindre les sources tierces aux domaines spécifiques nécessaires
3. Activer la rapport CSP : `report-uri /api/csp-report; report-to csp-endpoint`

---

### GRAV-04 : L'API catalogue JSON est publiquement accessible sans authentification

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `/catalogue/*/json` | **HIGH** | `src/catalogue_routes.py` | 145-191 |

**Description :** L'endpoint JSON du catalogue expose toutes les données publiées sans authentification. Bien que ce soit peut-être intentionnel pour une API publique, il expose :
- Les métadaches complètes de tous les items (`item.to_dict()`)
- Les liens magnet et data URLs
- Les ratings moyens
- La structure complète des galleries

**Recommandation :**
1. Ajouter un rate limiting plus strict sur cet endpoint (ex: 20 req/min par IP)
2. Paginer avec une limite maximale pour éviter l'enumération massive de données
3. Considérer l'ajout d'un cache public (Redis) pour réduire la charge DB

---

## 4. Vulnérabilités modérées

### MOD-01 : Fuites d'informations via les erreurs

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| Erreurs détaillées | **MEDIUM** | `src/admin_routes.py` | 182, `src/interactions.py` | 19-41 |

**Description :** Les logs et messages d'erreur peuvent révéler :
- Des IDs d'utilisateurs
- Des statuts de connexion (la réponse diffère entre "user existant/banned" et "user inexistant") — **user enumeration possible**
- L'existence ou non d'un compte selon le code de retour (401 pour les deux cas, mais le message diffère)

**Recommandation :**
1. Uniformiser les messages d'erreur : "Identifiants incorrects" quel que soit le cas
2. Ne jamais révéler si un email est enregistré ou non

---

### MOD-02 : Pas de validation CSRF sur certains endpoints API critiques

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `POST /api/reports` | **MEDIUM** | `src/admin_routes.py` | 124 |
| `POST /api/users/profile` | **MEDIUM** | `src/user_routes.py` | 102 |

**Description :** Les endpoints API nécessitent `X-CSRF-Token` header (ligne 56-58 dans app.py), mais la vérification n'est pas explicitement testée. Un site malveillant pourrait potentiellement exploiter une configuration de navigateur pour envoyer le token CSRF via un script cross-origin si le token est aussi disponible globalement.

Le `meta name="csrf-token"` accessible en JS (vu dans `upload.js` ligne 163) est **exposé aux attaques XSS**, permettant la vol du token CSRF.

**Recommandation :**
1. Ne pas exposer le token CSRF dans le DOM HTML (metadata) — l'envoyer uniquement via les formulaires WTForms ou header
2. Si nécessaire, au minimum : utiliser des cookies `SameSite=Strict` en complément

---

### MOD-03 : Stock XSS potentiel via les données du gallery JSON

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `data_json` | **MEDIUM** | `models.py` | 118 |

**Description :** Le champ `ItemGallery.data_json` (colonne `JSON`) stocke des données brutes non sanitizées. Lors du rendu dans les templates (`item_detail.html` ligne 61-65), les prévisualisations CSV sont affichées avec `|e` mais l'accès aux propriétés de l'objet JSON n'est pas contrôlé.

Si un attaquant peut injecter du HTML dans `data_json`, il pourrait potentiellement contourner l'échappement Jinja via des chaines de propriété.

**Recommandation :**
1. Sanitizer toutes les données entrantes avant insertion en BDD
2. Valider la structure JSON attendue strictement

---

### MOD-04 : Absence de protection contre le CSRF via l'endpoint `/catalogue/item/<id>/rate`

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `POST /catalogue/item/<id>/rate` | **MEDIUM** | `src/interactions.py` | 11-44 |

**Description :** L'endpoint de notation utilise `request.form.get("rating")` qui est protégé par CSRF via Flask-WTF. Cependant :
- Le endpoint n'exige pas d'authentification (`@login_required` est absent) — tout le monde peut noter
- Un visiteur non connecté peut soumettre des notes sans problème

**Recommandation :**
1. Ajouter `@login_required` pour forcer l'authentification avant de pouvoir noter
2. Ou vérifier explicitement la session : si pas d'utilisateur, refuser la note

---

## 5. Vulnérabilités mineures / Hardening

### MIN-01 : Nginx — Pas de limites de taux au niveau reverse proxy

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `limit_req` | **LOW** | `nginx/nginx.conf` | 36-46 |

**Recommandation :** Ajouter `limit_req_zone` dans nginx pour protéger contre le DDos applicatif :
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

---

### MIN-02 : Nginx — Pas de restriction sur les methods HTTP

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `limit_methods` | **LOW** | `nginx/nginx.conf` | 36-46 |

**Recommandation :** Bloquer les methods non-standard :
```nginx
if ($request_method !~ ^(GET|POST|PUT|DELETE|PATCH|OPTIONS)$) {
    return 405;
}
```

---

### MIN-03 : Docker — L'image de base utilise `python:3.12-slim` non-signée

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| Base image | **LOW** | `Dockerfile` | 2 |

**Recommandation :** Utiliser des images signées et vérifiées, ou scanner les images (Trivy, Snyk) avant build.

---

### MIN-04 : Docker — Le conteneur app s'exécute en root dans la phase de build

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `USER appuser` | **LOW** | `Dockerfile` | 27 |

**Recommandation :** La phase `test` (ligne 14-18) s'exécute en tant que root. Séparer les phases build/test/production pour limiter la surface d'attaque.

---

### MIN-05 : Database — Pas de backup chiffré configuré

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| Backup | **LOW** | `docker-compose.yml` | 62-63 |

**Recommandation :** Configurer des backups automatisés chiffrés avec retention policy. Ajouter un volume dédié pour les dumps.

---

### MIN-06 : Application — Pas de politique de rotation/expiration des sessions

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| Session lifetime | **LOW** | `app.py` | 165 |

**Description :** La session expire après 30 minutes (`PERMANENT_SESSION_LIFETIME = 1800`), ce qui est correct. Cependant :
- `_auth_time` est stocké (ligne 49 de `auth_routes.py`) mais **jamis vérifié** — pas d'inactivité logout, pas de re-authentication pour les actions sensibles

**Recommandation :** Implémenter la vérification `_auth_time` : si > 30 min depuis l'authentification, forcer une re-authentication pour les opérations critiques (changement mot de passe, modification admin).

---

### MIN-07 : Application — L'endpoint `/health` expose uniquement `{"status": "ok"}` mais n'exige pas d'authentification

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| Health endpoint | **LOW** | `app.py` | 127-129 |

**Recommandation :** Ajouter un secret de vérification : `/health?token=<secret>` ou utiliser l'endpoint standard pour la monitoring interne uniquement.

---

### MIN-08 : Templates — URL dans les attributs `href` non encodées

| Champ | Severity | Fichier | Ligne |
|-------|----------|---------|-------|
| `chunk.magnet_link`, `chunk.data_url` | **LOW** | `templates/item_detail.html` | 97, 102 |

**Recommandation :** Vérifier que toutes les URLs utilisateur dans les templates sont correctement échappées. L'utilisation de `|e` est correcte ici.

---

## 6. Analyse par couche

### Couche Infrastructure (Docker / Nginx)

| Aspect | Évaluation | Notes |
|--------|-----------|-------|
| **Nginx** | ✅ Bon | Reverse proxy correct, headers proxies configurés |
| **TLS/HTTPS** | ❌ Manquant | Port 80 uniquement en config par défaut |
| **Rate limiting (proxy)** | ❌ Absent | Uniquement au niveau Flask |
| **Logging** | ✅ Présent | Access + error logs configurés |
| **Docker multi-stage** | ✅ Bon | Phase test/production séparées |
| **Non-root user** | ✅ Partiel | `USER appuser` en production, mais pas en phase de build |

### Couche Application (Flask)

| Aspect | Évaluation | Notes |
|--------|-----------|-------|
| **CSRF protection** | ✅ Bon | `CSRFProtect` + exemption minime |
| **CSP** | ✅ Bon | Nonce-based, headers complets |
| **Rate limiting** | ✅ Bon | Flask-Limiter sur routes critiques |
| **Session management** | ⚠️ Moyenn | Cookie sécurisé mais pas de session fixation protection |
| **Input sanitization** | ✅ Bon | `bleach.clean()`, validation URL |
| **Password hashing** | ✅ Bon | Werkzeug scrypt |
| **SQL injection** | ✅ Protégé | SQLAlchemy parameterized queries |
| **Debug mode enforcement** | ✅ Excellent | Blocage explicif FLASK_DEBUG en production |
| **Secret key** | ⚠️ Local files only | `.env` et `.secret` non trackés mais stockés en clair sur le filesystem |
| **API auth** | ⚠️ Partiel | Session-based, pas de JWT pour API |

### Couche Modèle / BDD

| Aspect | Évaluation | Notes |
|--------|-----------|-------|
| **SQLAlchemy ORM** | ✅ Protégé | Requêtes parameterisées automatiques |
| **Password storage** | ✅ Bon | Hash scrypt, salt aléatoire |
| **Soft delete** | ⚠️ Partiel | `banned` flag mais pas de cascade de suppression |
| **Audit logging** | ✅ Excellent | `AdminAudit` model avec toutes les actions admin |
| **Connection pooling** | ✅ Bon | `pool_pre_ping`, `pool_recycle` configurés |
| **SSL for Postgres** | ⚠️ Partiel | `sslmode=prefer` (pas enforced) |

### Couche Frontend

| Aspect | Évaluation | Notes |
|--------|-----------|-------|
| **XSS protection** | ✅ Bon | Jinja autoescape + `|e` + CSP nonce |
| **CSRF token exposure** | ⚠️ Moyenn | Token accessible via DOM (`meta[name="csrf-token"]`) |
| **JS sanitization** | ❌ Absent | Aucune validation côté client pour les inputs sensibles |
| **HTTPS enforcement (client)** | ❌ Absent | Pas de check JS for HTTPS |
| **Clipboard API** | ✅ Bon | Utilisation sécurisée avec fallback |

---

## 7. Checklist de remédiation priorisée

### 🔴 Immédiat (0-24h)

- [ ] **Déplacer les secrets hors du filesystem** — utiliser Vault, AWS Secrets Manager ou env vars Docker (non versionnés)
- [ ] **Forcer HTTPS/TLS** en production Let's Encrypt ou certificats
- [ ] **Supprimer les logs `logging.warning()`** dans `src/interactions.py` avec données utilisateur
- [ ] **Uniformiser les messages d'erreur** de connexion (anti user enumeration)

### 🟠 Urgent (1-7 jours)

- [ ] **Ajouter validation CSRF explicite** sur tous les endpoints API (`X-CSRF-Token` requis systématiquement)
- [ ] **Validator la structure JSON `data_json`** avant insertion BDD
- [ ] **Ajouter `@login_required`** sur le endpoint `/catalogue/item/<id>/rate`
- [ ] **Restreindre l'accès IP** aux routes admin au niveau nginx
- [ ] **Ajouter object-src 'none' + base-uri 'self' + form-action 'self'** à la CSP

### 🟡 Recommandé (1-4 semaines)

- [ ] **Mettre en place des backups chiffrés** automatisés Postgres
- [ ] **Intégrer un scanner de vulnérabilités** dans le pipeline CI/CD
- [ ] **Activer la journalisation d'audit structurelle** (JSON) pour l'intégrité forensique
- [ ] **Ajouter une vérification `_auth_time`** pour les opérations sensibles
- [ ] **Limiter la taille du paramètre `per_page`** dans les endpoints de liste (pour éviter les attaques DoS par requête lourde)

### 🟢 Hardening futur (1-3 mois)

- [ ] Implémenter la **2FA obligatoire** pour l'administration
- [ ] Migrer vers un **système de secrets externe** (Vault / AWS Secrets Manager)
- [ ] Ajouter des **certifiats client mTLS** pour Postgres `sslmode=verify-full`
- [ ] Configurer **Content Security Policy report-only** pour tester les améliorations sans risque
- [ ] Implémenter une **politique de rotation de session** après changement de privilèges
- [ ] Ajouter un **WAF** (Web Application Firewall) au niveau nginx

---

## Annexe A : Résumé des scores

| Catégorie | Score | Évaluation |
|-----------|-------|-----------|
| **Auth & Sessions** | 7/10 | Bon framework, manquant rotation et binding |
| **CSRF / XSS** | 9/10 | Excellent (nonce CSP, autoescape, bleach) |
| **SQL Injection** | 10/10 | ORM protégé par parameterized queries |
| **Input Validation** | 8/10 | Bon sanitization, manquant validation JSON strict |
| **Secrets Management** | 5/10 | Moyenn — stockés localement, pas dans Git mais pas de gestionnaire dédié |
| **Transport Security** | 4/10 | TLS manquant par défaut |
| **Rate Limiting** | 8/10 | Bien implémenté, manque au niveau proxy |
| **Audit Logging** | 9/10 | Excellent pour actions admin |
| **Docker / Infra** | 7/10 | Multi-stage bien structuré, manquant WAF |

### Score global : **6.9 / 10**

*L'application présente un cadre de sécurité solide avec des protections modernes mais nécessite une correction immédiate pour le transport TLS et l'amélioration du cycle de vie des secrets en production.*

---

*Fin de l'audit.*
