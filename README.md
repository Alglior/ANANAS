# A.N.A.N.A.S.

Un portail de services géospatiaux basé sur des liens magnet et torrent pour le partage de données géographiques. Ce projet, développé avec Flask, fournit une interface web pour accéder aux données géospatiales via des liens de téléchargement décentralisés.

## Fonctionnalités

- Distribution de données géographiques via liens magnet
- Pages d'inscription et d'authentification des utilisateurs
- Formulaire de contact
- Protection CSRF (Flask-WTF)
- En-têtes de sécurité (X-Frame-Options DENY, X-Content-Type-Options nosniff)
- Cookies de session en mode HTTP-only
- Génération et validation automatique des clés secrètes

## Prérequis

Python 3.10+

- Flask == 3.1.0
- Flask-WTF == 1.2.1
- python-dotenv == 1.0.1
- gunicorn == 23.0.0

## Installation

Clonez le dépôt et créez un environnement virtuel :

```bash
python -m venv .venv
source .venv/bin/activate
```

Installez les dépendances :

```bash
pip install -r requirements.txt
```

Générez ou définissez une clé secrète :

```bash
export FLASK_SECRET_KEY="votre-cle-secrete"
```

Sinon, créez un fichier `.secret` avec le format suivant :

```text
FLASK_SECRET_KEY=votre-cle-secrete
```

Assurez-vous que le fichier dispose des permissions suivantes :

```bash
chmod 600 .secret
```

## Utilisation

Serveur de développement :

```bash
bash run.sh
```

Production avec gunicorn :

```bash
run_prod.sh
```

## Structure du projet

```text
app.py              - Point d'entrée de l'application Flask
requirements.txt    - Dépendances Python
run.sh             - Script d'exécution en mode développement
run_prod.sh        - Script d'exécution en production (gunicorn)
.secret            - Fichier de clé secrète (ignorer par Git, chmod 600)
static/            - Ressources statiques (CSS, JS, images)
templates/         - Templates Jinja2 HTML
```

## Configuration

| Variable         | Description                                       |
|------------------|---------------------------------------------------|
| FLASK_SECRET_KEY | Clé secrète de l'application pour CSRF/sessions   |
| FLASK_DEBUG      | Définir à 1 ou true pour activer le mode debug    |
| FLASK_ENV        | Définir à production dans un environnement de prod|
