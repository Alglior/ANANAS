# Plan : Suppression de l'email — Passage au système Discord-like (username + tag)

## Format du username
`prenom-nom-ab12#1234` → 2 lettres aléatoires + 4 chiffres = **6,76 millions combinaisons par nom**

## Exemple de rendu

```
┌─────────────────────────────────┐
│   Inscription                   │
├─────────────────────────────────┤
│                                 │
│   Prénom        ┌──────────┐    │
│                 │ Jean     │    │
│                 └──────────┘    │
│                                 │
│   Nom           ┌──────────┐    │
│                 │ Dupont   │    │
│                 └──────────┘    │
│                                 │
│   Mot de passe  ┌──────────┐    │
│                 │ •••••••• │    │
│                 └──────────┘    │
│                                 │
│   Votre identifiant unique :      │
│   ┌────────────────────────┐   │
│   │ jean-dupont-3f#7291   │   │
│   └────────────────────────┘   │
│   (généré automatiquement)     │
│                                 │
│   ┌──────────────────────┐     │
│   │   Créer mon compte   │     │
│   └──────────────────────┘     │
│                                 │
└─────────────────────────────────┘


┌─────────────────────────────────┐
│   Connexion                     │
├─────────────────────────────────┤
│                                 │
│   Identifiant   ┌──────────────┐│
│                 │ jean-dupont  ││
│                 │ -3f#7291     ││
│                 └──────────────┘│
│                                 │
│   Mot de passe  ┌──────────┐    │
│                 │ •••••••• │    │
│                 └──────────┘    │
│                                 │
│   ┌──────────────────────┐     │
│   │   Se connecter       │     │
│   └──────────────────────┘     │
│                                 │
└─────────────────────────────────┘


┌─────────────────────────────────┐
│   Profil public                 │
├─────────────────────────────────┤
│                                 │
│        ╭───────╮               │
│        │  JD   │               │
│        ╰───────╯               │
│                                 │
│     Jean Dupont                 │
│     jean-dupont-3f#7291         │
│                                 │
│   Membre depuis juillet 2026    │
│                                 │
│   12 publications · 5 commentaires
│                                 │
└─────────────────────────────────┘


┌─────────────────────────────────┐
│   Inviter dans une organisation │
├─────────────────────────────────┤
│                                 │
│   Identifiant   ┌──────────────┐│
│                 │ jean-dupont  ││
│                 │ -3f#7291     ││
│                 └──────────────┘│
│                                 │
│   ┌──────────┐                 │
│   │ Inviter  │                 │
│   └──────────┘                 │
│                                 │
└─────────────────────────────────┘
```

---

## Étape 1 — Migration base de données

**Fichier :** `alembic/versions/` + `app.py` (_run_migrations)

- Ajouter colonne `username` à la table `users` (VARCHAR, unique)
- Générer un username pour chaque utilisateur existant :
  ```python
  slug = f"{prenom}-{nom}".lower().strip()
  lettres = secrets.token_hex(1)  # 2 chars hex
  chiffres = random.randint(0, 9999)
  username = f"{slug}-{lettres}#{chiffres:04d}"
  ```
- Gérer les collisions (regénérer si déjà pris)
- Rendre `email` nullable (ou le garder pour le contact interne)

---

## Étape 2 — Modèle User

**Fichier :** `models.py`

- Ajouter `username: Mapped[str] = mapped_column(unique=True)`
- Optionnel : rendre `email` nullable (`Mapped[str | None]`)

---

## Étape 3 — Inscription

**Fichiers :** `src/auth_routes.py`, `templates/inscription.html`

- **Route POST** : supprimer le champ email du formulaire
- **Route POST** : générer le username automatiquement
- **Route POST** : créer l'utilisateur sans email
- **Template** : remplacer le champ email par un affichage du username généré ("Votre identifiant sera : jean-dupont-3f#7291")
- **Validation** : ne plus vérifier l'unicité de l'email

---

## Étape 4 — Connexion

**Fichiers :** `src/auth_routes.py`, `templates/connexion.html`

- **Route POST** : chercher l'utilisateur par `User.username` au lieu de `User.email`
- **Template** : remplacer le champ "Adresse e-mail" par "Identifiant"
- **Template** : changer le type du champ de `email` à `text`, changer le placeholder

---

## Étape 5 — Profil / Compte

**Fichiers :** `src/user_routes.py`, `templates/users/compte.html`, `templates/users/public_profile.html`, `static/js/users/compte.js`

- **Profil public** : afficher `username` au lieu d'email
- **Page compte** : supprimer la ligne email dans le header
- **Page compte** : supprimer le champ email du formulaire d'édition
- **API PUT /api/users/profile** : ne plus accepter/modifier l'email
- **JS compte.js** : ne plus envoyer l'email dans la requête PUT

---

## Étape 6 — Admin

**Fichiers :** `src/admin/__init__.py`, `src/admin/users.py`, `templates/admin/users.html`

- **Sérialisation admin** : remplacer `"email"` par `"username"` dans la réponse API
- **Audit (ban, unban, mute, warn, kick)** : logger le `username` au lieu de l'email
- **Template admin users** : remplacer la colonne email par username

---

## Étape 7 — Invitation organisation

**Fichiers :** `src/organization_routes.py`, `templates/organization_detail.html`, `static/js/organizations/detail.js`

- **API POST /api/organizations/<slug>/invite** : chercher par `User.username` au lieu de `User.email`
- **Template** : changer le champ email en champ username
- **JS** : envoyer `username` au lieu de `email`

---

## Étape 8 — Contact (inchangé)

**Fichiers :** `src/contact_routes.py`, `templates/contact.html`, `static/js/pages/contact.js`

- Le formulaire de contact **garde l'email** — c'est un autre besoin (contact, pas login)
- Laisser `ContactMessage.email` tel quel

---

## Étape 9 — Footer & Privacy

**Fichiers :** `templates/partials/footer.html`, `templates/privacy.html`

- Footer : inchangé (email de contact, pas login)
- Privacy : mettre à jour le texte pour mentionner le username au lieu de l'email

---

## Étape 10 — Seed data & Tests

**Fichiers :** `scripts/seed_data.py`, `scripts/seed_users.py`, `tests/conftest.py`, `tests/test_routes.py`, `tests/test_models.py`

- Ajouter un `username` à chaque user créé dans les seeds
- Mettre à jour les tests de connexion/inscription pour utiliser le username
- Mettre à jour le test de duplicat (vérifier l'unicité du username maintenant)

---

## Résumé des changements

| Fichier | Type | Changement |
|---------|------|-----------|
| `models.py` | Python | + `username`, `email` nullable |
| `alembic/versions/*.py` | Python | Migration SQL |
| `app.py` | Python | Auto-migration |
| `src/auth_routes.py` | Python | Login/Register par username |
| `src/user_routes.py` | Python | Profile sans email |
| `src/organization_routes.py` | Python | Invite par username |
| `src/admin/__init__.py` | Python | Série username |
| `src/admin/users.py` | Python | Audit username |
| `templates/connexion.html` | HTML | Champ identifiant |
| `templates/inscription.html` | HTML | Suppression email |
| `templates/users/compte.html` | HTML | Suppression email |
| `templates/users/public_profile.html` | HTML | Username au lieu d'email |
| `templates/admin/users.html` | HTML | Colonne username |
| `templates/organization_detail.html` | HTML | Invite par username |
| `static/js/users/compte.js` | JS | Profile sans email |
| `static/js/organizations/detail.js` | JS | Invite par username |
| `scripts/seed_data.py` | Python | + username |
| `scripts/seed_users.py` | Python | + username |
| `tests/` | Python | Tests adaptés |