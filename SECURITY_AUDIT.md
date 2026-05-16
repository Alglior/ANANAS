# Audit de Sécurité — A.N.A.N.A.S. (Site v2)

**Date :** 2026-05-16
**Cible :** Application Flask + PostgreSQL (SQLAlchemy ORM)
**État des lieux :** Analyse statique du code source et configuration

---

## Sommaire

1. [Fosses Critiques](#fosses-critiques)
2. [Fosses Haute Sévérité](#fosses-haute-sévérité)
3. [Fosses Moyenne Sévérité](#fosses-moyenne-sévérité)
4. [Fosses Basse Sévérité / Recommandations](#fosses-basse-sévérité--recommandations)
5. [Tableau Récapitulatif](#tableau-récapitulatif)

---

## Fosses Critiques

### 1. Contournement d'autorisation sur la vérification d'items (`src/interactions.py:70-90`)

L'endpoint `verify_item` ne vérifie **pas** si l'utilisateur est admin. N'importe quel utilisateur authentifié peut modifier le statut de vérification d'un item (passer à "verified"), contournant ainsi la fonctionnalité administrateur.

```python
# interactions.py:70-90
@bp.route("/api/items/<int:item_id>/verify", methods=["POST"])
@login_required
def verify_item(item_id):
    current_user = get_current_user()
    # ... PAS DE CHECK is_admin !
```

**Impact :** Un utilisateur malveillant peut se faire passer pour un modérateur et marquer du contenu comme "officiellement vérifié".

**Recommandation :** Ajouter au début de la fonction :
```python
if not current_user.is_admin:
    return jsonify({"error": "Non autorisé"}), 403
```

---

### 2. Création d'items sans vérification d'appartenance à l'organisation (`src/upload_routes.py:76-109`, `src/user_routes.py:245-330`)

Les endpoints de création d'item acceptent un `organization_id` fourni par le client, sans vérifier que l'utilisateur est membre de cette organisation.

```python
# upload_routes.py:88
organization_id = request.form.get("organization_id", type=int)
```

**Impact :** Un utilisateur peut publier des items au nom d'une autre organisation.

**Recommandation :** Vérifier qu'un `OrganizationMember` existe pour l'utilisateur et l'organisation cible, ou restreindre l'assignation aux seuls admins/owners.

---

### 3. Ajout de liens de visualisation sans vérification de propriété (`src/upload_routes.py:112-146`, `src/user_routes.py:333-365`)

Les deux endpoints `add_viz_link` permettent à tout utilisateur authentifié d'ajouter des liens de visualisation sur **n'importe quel item**, pas seulement ceux qu'il possède ou auxquels il est associé.

**Impact :** Un attaquant peut injecter des liens malveillants sur n'importe quel item du catalogue.

**Recommandation :** Vérifier que l'utilisateur est owner de l'item, membre de l'org associée, ou admin.

---

### 4. Auto-signalement d'items (`src/admin_routes.py:59-105`)

L'endpoint `create_report` ne vérifie pas si l'utilisateur signale son propre item. Un attaquant peut saturer la file de modération avec des faux signaux contre son propre contenu.

**Recommandation :** Comparer l'auteur de l'item avec l'utilisateur connectée et rejeter le signalement.

---

### 5. Identifiants de base de données en dur dans le code (`app.py:59-63`)

```python
db_uri = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}?sslmode=prefer"
# pg_pass = "password" (défaut)
```

Si les variables d'environnement ne sont pas définies, l'application utilise des identifiants par défaut faibles.

**Impact :** Accès non autorisé à la base de données si le fichier `.env` n'est pas correctement configuré en production.

**Recommandation :** Lever une erreur fatale si `SQLALCHEMY_DATABASE_URI` n'est pas fournie via variable d'environnement. Ne jamais utiliser de mots de passe par défaut.

---

## Fosses Haute Sévérité

### 6. Injection SQL LIKE (`src/user_routes.py:50`)

```python
Item.query.filter(Item.author_name.like(f"{current_user.prenom} {current_user.nom}%"))
```

Les caractères `%` et `_` dans les noms d'utilisateurs ne sont pas échappés. Un utilisateur avec un nom contenant `%` peut faire correspondre plusieurs items, ou exploiter le LIKE pour extraire des données par inference.

**Recommandation :** Utiliser `ilike` avec échappement explicite ou requête exacte via `==`.

---

### 7. Risque de fixation de session (`app.py:89`)

Après une connexion réussie, le cookie de session n'est pas renouvelé :

```python
session["user_id"] = user.id
```

**Recommandation :** Appeler `session.refresh()` après l'authentification pour régénérer l'ID de session.

---

### 8. Pas de rate limiting sur le changement de mot de passe (`src/user_routes.py:147-172`)

L'endpoint `/api/users/change-password` n'a pas de limite de requêtes. Un attaquant peut tenter des bruteforce pour deviner l'ancien mot de passe (la vérification exige que l'ancien mot de passe soit correct).

**Recommandation :** Ajouter `@limiter.limit("3 per hour")`.

---

### 9. Slug d'organisation non sanitizé (`src/organization_routes.py:23`)

```python
slug=name.lower().replace(" ", "-")
```

Pas de validation de longueur ni de caractères interdits. Un attaquant peut créer un slug très long (DoS) ou potentiellement problématique.

**Recommandation :** Valider la longueur (max 80), ne permettre que `[a-z0-9-]`, rejeter les caractères spéciaux.

---

### 10. Les pages admin retournent du JSON au lieu d'une erreur HTML (`src/admin_routes.py:170-215`)

Les routes `/admin/users` et `/admin/reports` utilisent `jsonify()` pour la réponse 403, ce qui casse l'affichage HTML pour les utilisateurs connectés mais non admins.

**Recommandation :** Utiliser `render_template()` avec une page d'erreur ou rediriger vers le homepage.

---

## Fosses Moyenne Sévérité

### 11. Énumération d'emails (`src/auth_routes.py:56-59`)

Lors de l'inscription, un message spécifique est affiché si l'email existe déjà : `Un compte avec cet e-mail existe déjà`. Cela permet à un attaquant de vérifier si un email est inscrit.

**Recommandation :** Utiliser un message générique indépendant du résultat (par exemple toujours rediriger vers la page de connexion avec une indication subtile).

---

### 12. Risque XSS dans l'affichage des noms d'utilisateurs

Les prénoms et noms sont stockés en texte brut sans sanitization et affichés directement dans les templates (profils, auteurs d'items, etc.). Bien que le contenu des commentaires soit sanitizé via `bleach`, les noms ne le sont pas. Un nom contenant `<script>` s'exécutera dans le navigateur des autres utilisateurs.

**Recommandation :** Activer l'autoescape sur les templates ou sanitizer les noms lors de la saisie.

---

### 13. Nom de l'auteur du commentaire non sanitizé (`src/interactions.py:53`)

```python
author_name = request.form.get("author", "").strip() or ...
```

Le nom est stocké en texte brut et affiché dans le HTML sans sanitization, contrairement au contenu du commentaire qui utilise `sanitize_html()`. C'est une vector XSS.

**Recommandation :** Appliquer `sanitize_html()` à `author_name`.

---

### 14. Contournement du rate limiting via proxy inverse

Le rate limiter utilise `get_remote_address` qui peut être contourné si l'application est derrière un reverse proxy (nginx, Docker) ne configurant pas correctement `X-Forwarded-For`.

**Recommandation :** Configurer le limiter avec `HEADERS=["X-Forwarded-For"]` et configurer les proxies de confiance.

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

### 19. La visibilité des DataChunks n'est pas appliquée dans les requêtes (`models.py:241`)

La colonne `visibility` existe mais aucune requête publique ne filtre les items avec `visibility != 'public'`. Des chunks privés pourraient être exposés via les API.

**Recommandation :** Ajouter un filtre systématique : `filter(DataChunk.visibility == 'public')` sur toutes les requêtes publiques.

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

| # | Sévérité | Titre | Fichier | Ligne(s) |
|---|----------|-------|---------|----------|
| 1 | 🔴 Critique | Contournement autorisation vérification item | `src/interactions.py` | 70-90 |
| 2 | 🔴 Critique | Création d'item sans appartenance org | `src/upload_routes.py`, `src/user_routes.py` | 76-109, 245-330 |
| 3 | 🔴 Critique | Ajout de viz-links sans propriété | `src/upload_routes.py`, `src/user_routes.py` | 112-146, 333-365 |
| 4 | 🔴 Critique | Auto-signalement d'items | `src/admin_routes.py` | 59-105 |
| 5 | 🔴 Critique | Identifiants DB en dur dans le code | `app.py` | 59-63 |
| 6 | 🟠 Haute | Injection SQL LIKE | `src/user_routes.py` | 50 |
| 7 | 🟠 Haute | Fixation de session | `app.py` | 89 |
| 8 | 🟠 Haute | Pas de rate limit sur changement mot de passe | `src/user_routes.py` | 147-172 |
| 9 | 🟠 Haute | Slug org non sanitizé / possible DoS | `src/organization_routes.py` | 23 |
| 10 | 🟠 Haute | Pages admin retournent JSON au lieu de HTML | `src/admin_routes.py` | 170-215 |
| 11 | 🟡 Moyenne | Énumération d'emails via inscription | `src/auth_routes.py` | 56-59 |
| 12 | 🟡 Moyenne | XSS affichage des noms utilisateurs | Templates / modèles | — |
| 13 | 🟡 Moyenne | XSS nom auteur commentaire non sanitizé | `src/interactions.py` | 53 |
| 14 | 🟡 Moyenne | Contournement rate limit via proxy | `app.py` | 48-52 |
| 15 | 🟢 Basse | Mode debug activable en production | `app.py` | 196 |
| 16 | 🟢 Basse | Pas de connection pooling DB | `app.py` | 57-66 |
| 17 | 🟢 Basse | SSL mode `prefer` au lieu de `require` | `app.py` | 63 |
| 18 | 🟢 Basse | Pas d'audit des actions admin | — | — |
| 19 | 🟢 Basse | Visibilité DataChunks ignorée dans requêtes | `models.py` / routes | — |
| 20 | 🟢 Basse | CSP utilise `'unsafe-inline'` | `app.py` | 105-112 |

---

## Priorité de correction recommandée

1. **Immédiat :** #1, #2, #3 — Contournements d'autorisation permettant des actions administratives
2. **Sprint suivant :** #4, #5, #6, #8 — Signalements auto, creds DB, injection SQL, bruteforce mots de passe
3. **Prochaines semaines :** #7, #9, #12, #13, #19 — Session fixation, slug DoS, XSS noms/auteurs, visibilité ignored
4. **Backlog / Hardening :** #10-#11, #14-#20 — Améliorations générales de configuration et défense en profondeur
