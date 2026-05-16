# Audit de Sécurité — A.N.A.N.A.S. (Site v2)

**Date :** 2026-05-16
**Cible :** Application Flask + PostgreSQL (SQLAlchemy ORM)
**État des lieux :** Analyse statique du code source et configuration
**Statut :** Corrections #1–#14 et #19 appliquées ✅

---

## Sommaire

1. [Fosses Critiques](#fosses-critiques)
2. [Fosses Haute Sévérité](#fosses-haute-sévérité)
3. [Fosses Moyenne Sévérité](#fosses-moyenne-sévérité)
4. [Fosses Basse Sévérité / Recommandations](#fosses-basse-sévérité--recommandations)
5. [Tableau Récapitulatif](#tableau-récapitulatif)
6. [Corrections Appliquées](#corrections-appliquées)

---

## Fosses Critiques

### ~~1.~~ ~~Contournement d'autorisation sur la vérification d'items (`src/interactions.py:70-90`)~~ ✅ CORRECTIF #1

~~L'endpoint `verify_item` ne vérifie **pas** si l'utilisateur est admin. N'importe quel utilisateur authentifié peut modifier le statut de vérification d'un item (passer à "verified"), contournant ainsi la fonctionnalité administrateur.~~

~~```python
# interactions.py:70-90
@bp.route("/api/items/<int:item_id>/verify", methods=["POST"])
@login_required
def verify_item(item_id):
    current_user = get_current_user()
    # ... PAS DE CHECK is_admin !
```~~

~~**Impact :** Un utilisateur malveillant peut se faire passer pour un modérateur et marquer du contenu comme "officiellement vérifié".~~

~~**Recommandation :** Ajouter au début de la fonction :~~
~~```python~~
~~if not current_user.is_admin:~~
~~    return jsonify({"error": "Non autorisé"}), 403~~
~~```~~

**Correctif appliqué (`src/interactions.py:76-77`) :**
```python
if not current_user.is_admin:
    return jsonify({"error": "Non autorisé"}), 403
```

---

### ~~2.~~ ~~Création d'items sans vérification d'appartenance à l'organisation (`src/upload_routes.py:76-109`, `src/user_routes.py:245-330`)~~ ✅ CORRECTIF #2

~~Les endpoints de création d'item acceptent un `organization_id` fourni par le client, sans vérifier que l'utilisateur est membre de cette organisation.~~

~~```python
# upload_routes.py:88
organization_id = request.form.get("organization_id", type=int)
```~~

~~**Impact :** Un utilisateur peut publier des items au nom d'une autre organisation.~~

~~**Recommandation :** Vérifier qu'un `OrganizationMember` existe pour l'utilisateur et l'organisation cible, ou restreindre l'assignation aux seuls admins/owners.~~

**Correctif appliqué (`src/upload_routes.py:97-106`, `src/user_routes.py:261-271`) :** Vérification active de `OrganizationMember.is_active` si l'utilisateur n'est pas admin. Seuls les membres actifs ou admins peuvent créer des items pour une organisation donnée.

---

### ~~3.~~ ~~Ajout de liens de visualisation sans vérification de propriété (`src/upload_routes.py:112-146`, `src/user_routes.py:333-365`)~~ ✅ CORRECTIF #3

~~Les deux endpoints `add_viz_link` permettent à tout utilisateur authentifié d'ajouter des liens de visualisation sur **n'importe quel item**, pas seulement ceux qu'il possède ou auxquels il est associé.~~

~~**Impact :** Un attaquant peut injecter des liens malveillants sur n'importe quel item du catalogue.~~

~~**Recommandation :** Vérifier que l'utilisateur est owner de l'item, membre de l'org associée, ou admin.~~

**Correctif appliqué (`src/upload_routes.py:132-133`, `src/user_routes.py:352-353`) :**
```python
if not user_owns_item_or_admin(current_user, item):
    return jsonify({"error": "Non autorisé"}), 403
```

---

### ~~4.~~ ~~Auto-signalement d'items (`src/admin_routes.py:59-105`)~~ ✅ CORRECTIF #4

~~L'endpoint `create_report` ne vérifie pas si l'utilisateur signale son propre item. Un attaquant peut saturer la file de modération avec des faux signaux contre son propre contenu.~~

~~**Recommandation :** Comparer l'auteur de l'item avec l'utilisateur connectée et rejeter le signalement.~~

**Correctif appliqué (`src/admin_routes.py:109-110`, `120-121`) :** Vérification que `reported_user.id != current_user.id` et que `item.author_name != full_name`. Les auto-signalements sont rejetés.

---

### ~~5.~~ ~~Identifiants de base de données en dur dans le code (`app.py:59-63`)~~ ✅ CORRECTIF #5

~~```python~~
~~db_uri = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}?sslmode=prefer"~~
~~# pg_pass = "password" (défaut)~~
~~```~~

~~Si les variables d'environnement ne sont pas définies, l'application utilise des identifiants par défaut faibles.~~

~~**Impact :** Accès non autorisé à la base de données si le fichier `.env` n'est pas correctement configuré en production.~~

~~**Recommandation :** Lever une erreur fatale si `SQLALCHEMY_DATABASE_URI` n'est pas fournie via variable d'environnement. Ne jamais utiliser de mots de passe par défaut.~~

**Correctif appliqué (`app.py:54-59`) :** Lancement d'un `RuntimeError` si `SQLALCHEMY_DATABASE_URI` n'est pas définie dans les variables d'environnement. Suppression des valeurs par défaut pour `pg_user`, `pg_pass`, `pg_host`, `pg_db`.

---

## Fosses Haute Sévérité

### ~~6.~~ ~~Injection SQL LIKE (`src/user_routes.py:50`)~~ ✅ CORRECTIF #6

~~```python~~
~~Item.query.filter(Item.author_name.like(f"{current_user.prenom} {current_user.nom}%"))~~
~~```~~

~~Les caractères `%` et `_` dans les noms d'utilisateurs ne sont pas échappés.~~

**Correctif appliqué (`src/user_routes.py:50`) :** La requête utilise maintenant `==` (égalité exacte) au lieu de `.like()`, ce qui préserve la parameterisation SQLAlchemy et élimine le risque d'injection SQL LIKE.

---

### ~~7.~~ ~~Risque de fixation de session (`app.py:89`)~~ ✅ CORRECTIF #7

~~Après une connexion réussie, le cookie de session n'est pas renouvelé :~~

~~```python~~
~~session["user_id"] = user.id~~
~~```~~

**Correctif appliqué (`app.py:86-91`) :** Le handler `connexion_post` appelle maintenant `session.clear()` avant de définir `user_id`, ce qui force la régénération complète du cookie de session après l'authentification. L'horodatage `_auth_time` est ajouté pour tracer le moment de l'authentification.

---

### ~~8.~~ ~~Pas de rate limiting sur le changement de mot de passe (`src/user_routes.py:147-172`)~~ ✅ CORRECTIF #8

~~L'endpoint `/api/users/change-password` n'a pas de limite de requêtes. Un attaquant peut tenter des bruteforce pour deviner l'ancien mot de passe (la vérification exige que l'ancien mot de passe soit correct).~~

~~**Recommandation :** Ajouter `@limiter.limit("3 per hour")`.~~

**Correctif appliqué (`src/user_routes.py:149`) :** Le décorateur `@limiter.limit("3 per hour")` est maintenant présent sur l'endpoint `/api/users/change-password`.

---

### ~~9.~~ ~~Slug d'organisation non sanitizé (`src/organization_routes.py:23`)~~ ✅ CORRECTIF #9

~~```python~~
~~slug=name.lower().replace(" ", "-")~~
~~```~~

~~Pas de validation de longueur ni de caractères interdits. Un attaquant peut créer un slug très long (DoS) ou potentiellement problématique.~~

~~**Recommandation :** Valider la longueur (max 80), ne permettre que `[a-z0-9-]`, rejeter les caractères spéciaux.~~

**Correctif appliqué (`src/organization_routes.py:13-20`, `32`) :** Fonction `sanitize_slug()` ajoutée — retire les caractères interdits, tronque à 80 caractères. Le nom est validé entre 2 et 100 caractères.

---

### ~~10.~~ ~~Les pages admin retournent du JSON au lieu d'une erreur HTML (`src/admin_routes.py:170-215`)~~ ✅ CORRECTIF #10

~~Les routes `/admin/users` et `/admin/reports` utilisent `jsonify()` pour la réponse 403, ce qui casse l'affichage HTML pour les utilisateurs connectés mais non admins.~~

~~**Recommandation :** Utiliser `render_template()` avec une page d'erreur ou rediriger vers le homepage.~~

**Correctif appliqué (`src/admin_routes.py:17-24`) :** Le décorateur `require_admin` retourne maintenant un template HTML via `render_template("error.html", ...)` au lieu de `jsonify()`.

---

## Fosses Moyenne Sévérité

### ~~11.~~ ~~Énumération d'emails (`src/auth_routes.py:56-59`)~~ ✅ CORRECTIF #11

~~Lors de l'inscription, un message spécifique est affiché si l'email existe déjà : `Un compte avec cet e-mail existe déjà`. Cela permet à un attaquant de vérifier si un email est inscrit.~~

**Correctif appliqué (`src/auth_routes.py:56-57`) :** En cas d'email déjà existant, la redirection vers la page de connexion se fait maintenant sans message explicite (pas de feedback indiquant l'existence ou non du compte). Cette réponse générique empêche l'énumération d'emails via le formulaire d'inscription.

---

### ~~12.~~ ~~Risque XSS dans l'affichage des noms d'utilisateurs~~ ✅ CORRECTIF #12

~~Les prénoms et noms sont stockés en texte brut sans sanitization et affichés directement dans les templates (profils, auteurs d'items, etc.). Bien que le contenu des commentaires soit sanitizé via `bleach`, les noms ne le sont pas. Un nom contenant `<script>` s'exécutera dans le navigateur des autres utilisateurs.~~

**Correctif appliqué (`src/auth_routes.py:45-46`, `src/user_routes.py:120-121`, `src/upload_routes.py:114`, `models.py:19`) :** Les champs `prenom` et `nom` sont maintenant sanitizés via `sanitize_html()` lors de la saisie (inscription, mise à jour du profil) et pour l'`author_name` des items. Cela élimine les données XSS malveillantes dès la insertion en base de données.

---

### ~~13.~~ ~~Nom de l'auteur du commentaire non sanitizé (`src/interactions.py:53`)~~ ✅ CORRECTIF #13

~~```python~~
~~author_name = request.form.get("author", "").strip() or ...~~
~~```~~

~~Le nom est stocké en texte brut et affiché dans le HTML sans sanitization, contrairement au contenu du commentaire qui utilise `sanitize_html()`. C'est un vecteur XSS.~~

**Correctif appliqué (`src/interactions.py:53-54`) :** Le nom de l'auteur est maintenant passé via `sanitize_html()` avant d'être stocké :
```python
raw_author = request.form.get("author", "").strip() or (f"{current_user.prenom} {current_user.nom}" if current_user else "")
author_name = sanitize_html(raw_author)
```

---

### ~~14.~~ ~~Contournement du rate limiting via proxy inverse~~ ✅ CORRECTIF #14

~~Le rate limiter utilise `get_remote_address` qui peut être contourné si l'application est derrière un reverse proxy (nginx, Docker) ne configurant pas correctement `X-Forwarded-For`.~~

**Correctif appliqué (`app.py:13-20`) :** Fonction `_get_client_ip()` ajoutée en tant que `key_func` du Limiter — elle lit d'abord l'en-tête `X-Forwarded-For`, et ne retombe sur `get_remote_address()` qu'en fallback. Cela permet au rate limiter de résoudre correctement l'IP client même derrière un proxy inverse.

---

## Fosses Basse Sévérité / Recommandations

### 15. Mode debug activable en production (`app.py:196`)

```python
debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
```

La valeur par défaut est `"false"`, ce qui est sûr, mais il n'y a pas d'enforce pour empêcher accidentellement `debug=true` en production.

**Recommandation :** Ajouter un check explicite : refuser de démarrer si `debug=True` et `FLASK_ENV=production`.

---

### 16. Pas de configuration de connection pooling PostgreSQL

Les paramètres de pool de connexion ne sont pas configurés. Sous charge, cela peut causer une exhaustion des connexions.

**Recommandation :** Ajouter `connect_timeout=10` et configurer le pool via SQLAlchemy (eg. `QueuePool`).

---

### 17. SSL en mode `prefer` (`app.py:63`)

```
sslmode=prefer
```

Le mode `prefer` autorise les connexions non-chiffrées si le serveur accepte. Doit être `require` ou `verify-full`.

**Recommandation :** Passer à `sslmode=require` en production.

---

### 18. Pas de journalisation des actions admin

Les bans/unbans et résolutions de signalement ne sont loggées que dans le champ `reviewed_by` du tableau `reports`. Les actions de ban n'enregistrent pas quel admin les a effectuées.

**Recommandation :** Créer une table `admin_actions` pour auditor toutes les opérations administratives (qui, quand, quelle action, sur quoi).

---

### ~~19.~~ ~~La visibilité des DataChunks n'est pas appliquée dans les requêtes~~ ✅ CORRECTIF #19

~~La colonne `visibility` existe mais aucune requête publique ne filtre les items avec `visibility != 'public'`. Des chunks privés pourraient être exposés via les API.~~

**Correctif appliqué (`models.py:77`) :** La requête de DataChunks dans `Item.to_dict()` est maintenant filtrée par `visibility="public"` :
```python
DataChunk.query.filter_by(parent_item_id=self.id, visibility="public").all()
```

---

### 20. CSP Content-Security-Policy utilise `'unsafe-inline'` (`app.py:105-112`)

```
script-src 'self' 'unsafe-inline' https://unpkg.com;
style-src 'self' 'unsafe-inline' ...
```

L'utilisation de `'unsafe-inline'` dans `script-src` et `style-src` réduit l'efficacité du CSP contre les attaques XSS.

**Recommandation :** Remplacer par des hashes nonces pour les scripts/styles internes et supprimer `'unsafe-inline'`.

---

## Tableau Récapitulatif

| # | Sévérité | Titre | Fichier | Ligne(s) | Statut |
|---|----------|-------|---------|----------|--------|
| ~~1~~ | 🔴 Critique | ~~Contournement autorisation vérification item~~ | `src/interactions.py` | ~~70-90~~ | ✅ **CORRIGÉ** |
| ~~2~~ | 🔴 Critique | ~~Création d'item sans appartenance org~~ | `src/upload_routes.py`, `src/user_routes.py` | ~~76-109, 245-330~~ | ✅ **CORRIGÉ** |
| ~~3~~ | 🔴 Critique | ~~Ajout de viz-links sans propriété~~ | `src/upload_routes.py`, `src/user_routes.py` | ~~112-146, 333-365~~ | ✅ **CORRIGÉ** |
| ~~4~~ | 🔴 Critique | ~~Auto-signalement d'items~~ | `src/admin_routes.py` | ~~59-105~~ | ✅ **CORRIGÉ** |
| ~~5~~ | 🔴 Critique | ~~Identifiants DB en dur dans le code~~ | `app.py` | ~~59-63~~ | ✅ **CORRIGÉ** |
| ~~6~~ | 🟠 Haute | ~~Injection SQL LIKE~~ | `src/user_routes.py` | ~~50~~ | ✅ **CORRIGÉ** |
| ~~7~~ | 🟠 Haute | ~~Session fixation~~ | `app.py` | ~~89~~ | ✅ **CORRIGÉ** |
| ~~8~~ | 🟠 Haute | ~~Pas de rate limit sur changement mot de passe~~ | `src/user_routes.py` | ~~147-172~~ | ✅ **CORRIGÉ** |
| ~~9~~ | 🟠 Haute | ~~Slug org non sanitizé / possible DoS~~ | `src/organization_routes.py` | ~~23~~ | ✅ **CORRIGÉ** |
| ~~10~~ | 🟠 Haute | ~~Pages admin retournent JSON au lieu de HTML~~ | `src/admin_routes.py` | ~~170-215~~ | ✅ **CORRIGÉ** |
| ~~11~~ | 🟡 Moyenne | ~~Énumération d'emails via inscription~~ | `src/auth_routes.py` | ~~56-59~~ | ✅ **CORRIGÉ** |
| ~~12~~ | 🟡 Moyenne | ~~XSS affichage des noms utilisateurs~~ | `src/auth_routes.py`, `src/user_routes.py`, `models.py` | — | ✅ **CORRIGÉ** |
| ~~13~~ | 🟡 Moyenne | ~~XSS nom auteur commentaire non sanitizé~~ | `src/interactions.py` | 53 | ✅ **CORRIGÉ** |
| ~~14~~ | 🟡 Moyenne | ~~Contournement rate limit via proxy~~ | `app.py` | 13-20 | ✅ **CORRIGÉ** |
| 15 | 🟢 Basse | Mode debug activable en production | `app.py` | 196 | ⚪ ouvert |
| 16 | 🟢 Basse | Pas de connection pooling DB | `app.py` | 57-66 | ⚪ ouvert |
| 17 | 🟢 Basse | SSL mode `prefer` au lieu de `require` | `app.py` | 63 | ⚪ ouvert |
| 18 | 🟢 Basse | Pas d'audit des actions admin | — | — | ⚪ ouvert |
| ~~19~~ | 🟢 Basse | ~~Visibilité DataChunks ignorée dans requêtes~~ | `models.py` | 77 | ✅ **CORRIGÉ** |
| 20 | 🟢 Basse | CSP utilise `'unsafe-inline'` | `app.py` | 105-112 | ⚪ ouvert |

---

## Corrections Appliquées

| # | Correctif | Fichier | Ligne |
|---|-----------|---------|-------|
| #1 | Ajout du check `is_admin` sur `verify_item` | `src/interactions.py` | 76-77 |
| #2 | Vérification `OrganizationMember.is_active` à la création d'item | `src/upload_routes.py`, `src/user_routes.py` | 97-106, 261-271 |
| #3 | Check `user_owns_item_or_admin()` sur `add_viz_link` | `src/upload_routes.py`, `src/user_routes.py` | 132-133, 352-353 |
| #4 | Prévention des auto-signalements | `src/admin_routes.py` | 109-110, 120-121 |
| #5 | Erreur fatale si `SQLALCHEMY_DATABASE_URI` non défini | `app.py` | 54-59 |
| #6 | Remplacement `.like()` par `==` (égalité exacte, parameterisée) | `src/user_routes.py` | 50 |
| #7 | `session.clear()` avant `user_id` après connexion réussie | `app.py` | 86-91 |
| #8 | Rate limiter `@limiter.limit("3 per hour")` sur change-password | `src/user_routes.py` | 149 |
| #11 | Redirect générique vers `/connexion` au lieu d'erreur email existant | `src/auth_routes.py` | 56-57 |
| #9 | Fonction `sanitize_slug()` + validation du nom (2-100 chars) | `src/organization_routes.py` | 13-20, 32 |
| #10 | Décorateur `require_admin` retourne HTML via `render_template` | `src/admin_routes.py` | 17-24 |
| #12 | Sanitisation `sanitize_html()` sur prenom/nom (inscription + profil) | `src/auth_routes.py`, `src/user_routes.py`, `models.py` | 45-46, 120-121, 19 |
| #13 | Sanitisation `sanitize_html()` sur le nom d'auteur des commentaires | `src/interactions.py` | 53-54 |
| #14 | Fonction `_get_client_ip()` lit `X-Forwarded-For` pour le limiter | `app.py` | 13-20 |
| #19 | Filtre `visibility="public"` dans la requête DataChunks de `to_dict()` | `models.py` | 77 |

---

## Priorité de correction recommandée

1. **Sprint suivant :** ~~#6, #7, #8, #11~~ ✅ Terminé — Injection SQL LIKE, session fixation, rate limit password change, énumération d'emails
2. **Prochaines semaines :** ~~#12, #13, #14, #19~~ ✅ Terminé — XSS noms/auteurs, rate limit proxy, visibilité DataChunks
3. **Backlog / Hardening :** #15-#18, #20 — Debug mode, connection pooling, SSL, audit admin, CSP

---
