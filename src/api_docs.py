import os
import urllib.parse

from flask import Blueprint, render_template

bp = Blueprint("api_docs", __name__)

BASE = os.environ.get("SITE_URL", "https://ananas.example.com")


def _examples(method, path, body=None, auth=False, form=False, multipart=False):
    url = BASE + path
    curl_headers = []
    py_headers = {}
    js_headers = {}

    if auth:
        curl_headers.append('-H "X-CSRF-Token: <token>"')
        py_headers["X-CSRF-Token"] = "<token>"
        js_headers["X-CSRF-Token"] = "<token>"

    has_body = body or method in ("POST", "PUT")

    if multipart:
        h = " \\\n  ".join(curl_headers)
        curl_body = f" \\\n  -F '{body}'" if body else ""
        curl = f"curl -X {method} \\\n  '{url}'" + (f" \\\n  {h}" if h else "") + curl_body

        files = "{" + body + "}" if body else "{}"
        py_h = f", headers={py_headers}" if py_headers else ""
        py = f"import requests\n\nresponse = requests.{method.lower()}('{url}', files={files}{py_h})"

        js_h = f", {js_headers}".replace("'", '"') if js_headers else ""
        js_body = ", body: new FormData()" if body else ""
        js = f"fetch('{url}', {{\n  method: '{method}'{js_h}{js_body}\n}})"

    elif form:
        h = " \\\n  ".join(curl_headers)
        curl_body = f" \\\n  -d '{body}'" if body else ""
        curl = f"curl -X {method} \\\n  '{url}'" + (f" \\\n  {h}" if h else "") + curl_body

        d = {k: v[0] for k, v in urllib.parse.parse_qs(body).items()} if body else {}
        py_data = f"data={d}"
        py_h = f", headers={py_headers}" if py_headers else ""
        py = f"import requests\n\nresponse = requests.{method.lower()}('{url}', {py_data}{py_h})"

        js_h = f", {js_headers}".replace("'", '"') if js_headers else ""
        js_body = f", body: '{body}'" if body else ""
        js = f"fetch('{url}', {{\n  method: '{method}'{js_h}{js_body}\n}})"

    else:
        content_type = '-H "Content-Type: application/json"'
        if has_body:
            curl_headers.append(content_type)
            py_headers["Content-Type"] = "application/json"
            js_headers["Content-Type"] = "application/json"

        h = " \\\n  ".join(curl_headers)
        curl_body = f" \\\n  -d '{body}'" if body else (" \\\n  -d '{}'" if has_body and method != "POST" else "")
        curl = f"curl -X {method} \\\n  '{url}'" + (f" \\\n  {h}" if h else "") + curl_body

        py_data = f", json={body}" if body else (", json={}" if has_body and method not in ("POST",) else "")
        py_h = f", headers={py_headers}" if py_headers else ""
        py = f"import requests\n\nresponse = requests.{method.lower()}('{url}'{py_data}{py_h})"

        js_h = f", {js_headers}".replace("'", '"') if js_headers else ""
        js_body = f", body: JSON.stringify({body})" if body else (", body: '{}'" if has_body and method != "POST" else "")
        js = f"fetch('{url}', {{\n  method: '{method}'{js_h}{js_body}\n}})"

    return [
        {"lang": "curl", "code": curl},
        {"lang": "python", "code": py},
        {"lang": "javascript", "code": js},
    ]


_ENDPOINTS = [
    {"method": "POST", "path": "/connexion", "desc": "Connecter un utilisateur (pseudo + mot de passe)", "auth": False, "rate": "5/h",
     "form": True,
     "body": "pseudo=john-doe%23ab7f3c&password=********"},
    {"method": "POST", "path": "/inscription", "desc": "Creer un compte (prenom, nom, mot de passe)", "auth": False, "rate": "3/h",
     "form": True,
     "body": "prenom=John&nom=Doe&password=Str0ng%21Pass"},
    {"method": "GET",  "path": "/logout", "desc": "Deconnecter et detruire la session", "auth": True, "rate": None},
    {"method": "POST", "path": "/connexion/2fa", "desc": "Verifier le code de la 2FA lors de la connexion", "auth": False, "rate": "5/h",
     "form": True,
     "body": "token=123456"},
    {"method": "GET", "path": "/catalogue/<type>", "desc": "Catalogue pagine (types: donnees, cartes, applications)", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/<type>/<page>", "desc": "Page specifique du catalogue", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/<type>/<page>/json", "desc": "Catalogue au format JSON", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/<type>/recherche-avancee", "desc": "Recherche avancee par etiquettes", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>", "desc": "Page de detail d'un element", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/data", "desc": "Onglet donnees (geodonnees uniquement)", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/gallery", "desc": "Onglet galerie / reutilisation", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/comments/json", "desc": "Commentaires pagines (JSON)", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/magnets/download", "desc": "Telecharger tous les liens magnet (fichier .magnet)", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/details/json", "desc": "Details complets (liens de visualisation, chunks)", "auth": False, "rate": None},
    {"method": "GET", "path": "/api/items/<id>/image-status", "desc": "Statut de téléchargement des images (suivi par aimant: statut, progression)", "auth": False, "rate": None},
    {"method": "POST", "path": "/catalogue/item/<id>/rate", "desc": "Noter un element (1-5 etoiles)", "auth": True, "rate": None,
     "form": True,
     "body": "rating=4"},
    {"method": "POST", "path": "/catalogue/item/<id>/comment", "desc": "Ajouter un commentaire", "auth": True, "rate": None,
     "form": True,
     "body": "text=Tres+utile%2C+merci+%21"},
    {"method": "POST", "path": "/api/catalogue/item/<id>/reply", "desc": "Repondre a un commentaire", "auth": True, "rate": None,
     "body": '{"content": "Je confirme !", "parent_id": 42}'},
    {"method": "POST", "path": "/api/items/<id>/viz-links", "desc": "Ajouter un lien de visualisation", "auth": True, "rate": None,
     "body": '{"name": "Carte interactive", "url": "https://...", "link_type": "external"}'},
    {"method": "POST", "path": "/api/items/<id>/verify", "desc": "Modifier le statut de verification (verified / unofficial / rejected)", "auth": True, "rate": None,
     "body": '{"status": "verified", "notes": "Donnees conformes"}'},
    {"method": "POST", "path": "/api/items/<id>/unpublish", "desc": "Retirer une publication (remet en brouillon)", "auth": True, "rate": None},
    {"method": "GET",  "path": "/profile/<user_id>", "desc": "Profil public d'un utilisateur", "auth": False, "rate": None},
    {"method": "GET",  "path": "/compte", "desc": "Tableau de bord (infos, securite, activite)", "auth": True, "rate": None},
    {"method": "GET",  "path": "/upload", "desc": "Page de formulaire d'upload", "auth": True, "rate": None},
    {"method": "GET",  "path": "/brouillons", "desc": "Page de gestion des brouillons", "auth": True, "rate": None},
    {"method": "PUT",  "path": "/api/users/profile", "desc": "Modifier son prenom / nom", "auth": True, "rate": None,
     "body": '{"prenom": "Jean", "nom": "Dupont"}'},
    {"method": "POST", "path": "/api/users/change-password", "desc": "Changer son mot de passe", "auth": True, "rate": "5/h",
     "body": '{"current_password": "OldPass1!", "new_password": "NewStr0ng!"}'},
    {"method": "POST", "path": "/api/users/2fa/setup", "desc": "Configurer la 2FA (retourne le secret et le QR code)", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/users/2fa/enable", "desc": "Activer la 2FA avec le code de validation", "auth": True, "rate": None,
     "body": '{"code": "123456"}'},
    {"method": "POST", "path": "/api/users/2fa/disable", "desc": "Desactiver la 2FA (mot de passe requis)", "auth": True, "rate": None,
     "body": '{"code": "123456", "password": "MotDePasse1!"}'},
    {"method": "POST", "path": "/api/users/generate-recovery-codes", "desc": "Generer 10 codes de recuperation", "auth": True, "rate": "30/h"},
    {"method": "POST", "path": "/api/users/avatar", "desc": "Uploader un avatar (png/jpg/webp)", "auth": True, "rate": None,
     "multipart": True,
     "body": "avatar=@mon_avatar.png"},
    {"method": "POST", "path": "/api/upload/file", "desc": "Uploader un fichier", "auth": True, "rate": None,
     "form": True,
     "body": "title=Ma+donnee&type=geodonnee&format_type=csv&description=Description&data_format_level=simple"},
    {"method": "POST", "path": "/api/upload/item", "desc": "Creer un element", "auth": True, "rate": None,
     "body": '{"title": "Ma donnee", "type": "geodonnee", "description": "...", "magnet_link": "magnet:?...", "format_type": "GeoJSON"}'},
    {"method": "PUT",  "path": "/api/upload/item/<id>", "desc": "Modifier un brouillon", "auth": True, "rate": None,
     "body": '{"title": "Titre mis a jour", "description": "..."}'},
    {"method": "DELETE", "path": "/api/upload/item/<id>", "desc": "Mettre a la corbeille", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/upload/item/<id>/publish", "desc": "Publier un brouillon", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/upload/item/<id>/restore", "desc": "Restaurer depuis la corbeille", "auth": True, "rate": None},
    {"method": "DELETE", "path": "/api/upload/item/<id>/purge", "desc": "Supprimer definitivement", "auth": True, "rate": None},
    {"method": "GET",  "path": "/api/upload/drafts", "desc": "Brouillons (pagine)", "auth": True, "rate": None},
    {"method": "DELETE", "path": "/api/upload/drafts/all", "desc": "Mettre tous les brouillons a la corbeille", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/upload/drafts/publish", "desc": "Publier tous les brouillons", "auth": True, "rate": None},
    {"method": "GET",  "path": "/api/upload/trash", "desc": "Corbeille (pagine)", "auth": True, "rate": None},
    {"method": "DELETE", "path": "/api/upload/trash/all", "desc": "Vider la corbeille (suppression definitive)", "auth": True, "rate": None},
    {"method": "GET",  "path": "/api/upload/publications", "desc": "Publications (pagine)", "auth": True, "rate": None},
    {"method": "DELETE", "path": "/api/upload/publications/all", "desc": "Retirer toutes les publications", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/upload/publications/verify", "desc": "Verifier toutes ses publications (admin)", "auth": True, "rate": None},
    {"method": "GET",    "path": "/organizations", "desc": "Liste des organisations", "auth": False, "rate": None},
    {"method": "GET",    "path": "/organizations/<page>", "desc": "Page suivante de la liste des organisations", "auth": False, "rate": None},
    {"method": "GET",    "path": "/organizations/<slug>/items", "desc": "Items publics d'une organisation", "auth": False, "rate": None},
    {"method": "GET",    "path": "/organizations/<slug>", "desc": "Detail d'une organisation", "auth": False, "rate": None},
    {"method": "POST",   "path": "/api/organizations", "desc": "Creer une organisation", "auth": True, "rate": None,
     "body": '{"name": "Ma Super Organisation", "slug": "ma-super-org", "description": "..."}'},
    {"method": "POST",   "path": "/api/organizations/<slug>/join", "desc": "Rejoindre une organisation", "auth": True, "rate": None},
    {"method": "GET",    "path": "/api/organizations/<slug>/requests", "desc": "Lister les demandes d'acces", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/requests/<request_id>/approve", "desc": "Accepter une demande d'acces", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/requests/<request_id>/reject", "desc": "Refuser une demande d'acces", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/leave", "desc": "Quitter une organisation", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/members/<user_id>/role", "desc": "Modifier le role d'un membre", "auth": True, "rate": None,
     "body": '{"role": "editor"}'},
    {"method": "DELETE", "path": "/api/organizations/<slug>/members/<user_id>", "desc": "Retirer un membre", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/invite", "desc": "Inviter un membre par pseudo", "auth": True, "rate": None,
     "body": '{"pseudo": "username"}'},
    {"method": "GET",    "path": "/api/organizations/<slug>/roles", "desc": "Lister les roles personnalises", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/roles", "desc": "Creer un role personnalise", "auth": True, "rate": None,
     "body": '{"name": "Editeur", "permissions": ["manage_items"]}'},
    {"method": "PUT",    "path": "/api/organizations/<slug>/roles/<role_id>", "desc": "Modifier un role", "auth": True, "rate": None,
     "body": '{"name": "Super Editeur", "permissions": ["manage_items", "invite_members"]}'},
    {"method": "DELETE", "path": "/api/organizations/<slug>/roles/<role_id>", "desc": "Supprimer un role", "auth": True, "rate": None},
    {"method": "DELETE", "path": "/api/organizations/<slug>", "desc": "Supprimer l'organisation", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/reports", "desc": "Signaler un contenu (spam, fausses donnees, autre)", "auth": True, "rate": None,
     "body": '{"target_type": "geodonnee", "target_id": 42, "reason": "fake_data", "description": "..."}'},
    {"method": "POST", "path": "/api/contact", "desc": "Envoyer un message de contact", "auth": True, "rate": "5/h",
     "body": '{"name": "Jean", "email": "jean@example.com", "subject": "Question", "message": "Bonjour, ..."}'},
    {"method": "GET", "path": "/changelog", "desc": "Historique des mises a jour de la plateforme", "auth": False, "rate": None},
    {"method": "GET", "path": "/feuille-de-route", "desc": "Feuille de route : fonctionnalites prevues et visions long terme", "auth": False, "rate": None},
    {"method": "GET", "path": "/rapport", "desc": "Rapports et documents publies", "auth": False, "rate": None},
    {"method": "GET", "path": "/rapport/pdf/<filename>", "desc": "Telecharger / visualiser un rapport PDF", "auth": False, "rate": None},
    {"method": "GET", "path": "/docs", "desc": "Index de la documentation", "auth": False, "rate": None},
    {"method": "GET", "path": "/docs/<slug>", "desc": "Page de documentation (slugs: api-protocoles, guide-utilisation, ...)", "auth": False, "rate": None},
    {"method": "GET", "path": "/apropos", "desc": "Page A propos", "auth": False, "rate": None},
    {"method": "GET", "path": "/contact", "desc": "Page du formulaire de contact", "auth": False, "rate": None},
    {"method": "GET", "path": "/mentions-legales", "desc": "Mentions legales", "auth": False, "rate": None},
    {"method": "GET", "path": "/conditions-utilisation", "desc": "Conditions d'utilisation", "auth": False, "rate": None},
    {"method": "GET", "path": "/confidentialite", "desc": "Politique de confidentialite", "auth": False, "rate": None},
    {"method": "GET", "path": "/health", "desc": "Sante de l'application (healthcheck)", "auth": False, "rate": None},
    {"method": "GET",    "path": "/admin/accueil", "desc": "Tableau de bord administrateur", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/users", "desc": "Gestion des utilisateurs", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/users/<page>", "desc": "Pagination de la gestion des utilisateurs", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/users/<id>/ban", "desc": "Bannir / debannir / tempban / mute / warn / kick", "auth": True, "rate": None, "admin": True,
     "body": '{"action": "ban", "reason": "Non respect des CGU"}'},
    {"method": "GET",    "path": "/api/users/banned", "desc": "Liste des utilisateurs bannis", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/reports", "desc": "Gestion des signalements", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/reports/<id>/resolve", "desc": "Resoudre / rejeter un signalement", "auth": True, "rate": None, "admin": True,
     "body": '{"status": "resolved", "notes": "Fausse alerte"}'},
    {"method": "GET",    "path": "/admin/moderation", "desc": "Moderation des contenus", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/comments/<id>", "desc": "Supprimer un commentaire", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/items/<id>", "desc": "Supprimer un element", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/items/<id>/verify", "desc": "Verifier un element", "auth": True, "rate": None, "admin": True,
     "body": '{"notes": "Donnees conformes"}'},
    {"method": "POST",   "path": "/api/admin/items/<id>/unverify", "desc": "Deverifier un element", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/audit", "desc": "Journal d'audit", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/contact-messages", "desc": "Messages de contact", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/mirrors", "desc": "Sites miroirs", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/featured", "desc": "Elements a la une", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/geopackages", "desc": "GeoPackages", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/catalogues", "desc": "Activation des catalogues", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/replication", "desc": "Replication de catalogue distant", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/tags", "desc": "Gestion des tags predefinis", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/settings", "desc": "Parametres du site (fichiers simples, 2FA, accueil)", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/backup", "desc": "Sauvegardes de la base de donnees", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/qbittorrent", "desc": "Statut du client BitTorrent", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/changelog", "desc": "Edition de la page des mises a jour", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/qbittorrent/status", "desc": "Statut de qBittorrent (transfert + torrents)", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/qbittorrent/cleanup", "desc": "Nettoyer les torrents orphelins", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/simple-files", "desc": "Lister les fichiers simples", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/simple-files", "desc": "Ajouter un fichier simple", "auth": True, "rate": None, "admin": True},
    {"method": "PUT",    "path": "/api/admin/simple-files/<id>", "desc": "Modifier un fichier simple", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/simple-files/<id>", "desc": "Supprimer un fichier simple", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/mirrors", "desc": "Lister les sites miroirs", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/mirrors", "desc": "Creer un site miroir", "auth": True, "rate": None, "admin": True},
    {"method": "PUT",    "path": "/api/admin/mirrors/<id>", "desc": "Modifier un site miroir", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/mirrors/<id>", "desc": "Supprimer un site miroir", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/featured", "desc": "Lister les elements a la une", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/featured", "desc": "Mettre un element a la une", "auth": True, "rate": None, "admin": True},
    {"method": "PUT",    "path": "/api/admin/featured/<id>", "desc": "Modifier un element a la une", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/featured/<id>", "desc": "Retirer un element de la une", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/geopackages", "desc": "Lister les GeoPackages", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/geopackages", "desc": "Creer un GeoPackage", "auth": True, "rate": None, "admin": True},
    {"method": "PUT",    "path": "/api/admin/geopackages/<id>", "desc": "Modifier un GeoPackage", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/geopackages/<id>", "desc": "Supprimer un GeoPackage", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/contact-messages", "desc": "Lister les messages de contact", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/contact-messages/<id>/read", "desc": "Marquer un message comme lu / non lu", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/contact-messages/<id>", "desc": "Supprimer un message de contact", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/audit", "desc": "Donnees du journal d'audit", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/items", "desc": "Elements avec filtres (moderation)", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/items/search", "desc": "Recherche d'elements", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/comments", "desc": "Commentaires avec filtres (moderation)", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/reports", "desc": "Signalements avec filtres", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/catalogues/<catalogue_type>/toggle", "desc": "Activer / desactiver un catalogue", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/api/admin/tags", "desc": "Lister les tags predefinis", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/tags", "desc": "Creer une categorie de tags", "auth": True, "rate": None, "admin": True},
    {"method": "PUT",    "path": "/api/admin/tags/<id>", "desc": "Modifier une categorie de tags", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/tags/<id>", "desc": "Supprimer une categorie de tags", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/tags/<id>/tags", "desc": "Ajouter un tag dans une categorie", "auth": True, "rate": None, "admin": True},
    {"method": "PUT",    "path": "/api/admin/tags/<id>/tags/<tag_id>", "desc": "Modifier un tag", "auth": True, "rate": None, "admin": True},
    {"method": "DELETE", "path": "/api/admin/tags/<id>/tags/<tag_id>", "desc": "Supprimer un tag", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/settings/update", "desc": "Mettre a jour les parametres du site", "auth": True, "rate": None, "admin": True,
     "body": '{"home_show_simple_files": true}'},
    {"method": "POST",   "path": "/api/admin/settings/logo-upload", "desc": "Uploader le logo du site", "auth": True, "rate": None, "admin": True,
     "multipart": True,
     "body": "logo=@logo.png"},
    {"method": "GET",    "path": "/api/admin/backup/download", "desc": "Telecharger une sauvegarde", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/backup/restore", "desc": "Restaurer une sauvegarde", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/replication/preview", "desc": "Apercu de la replication distante", "auth": True, "rate": None, "admin": True},
    {"method": "POST",   "path": "/api/admin/replication/fetch", "desc": "Lancer la replication distante", "auth": True, "rate": None, "admin": True},
]


CATEGORIES = [
    {"name": "Authentification", "keys": [("POST", "/connexion"), ("POST", "/inscription"), ("GET", "/logout"),
                                          ("POST", "/connexion/2fa")]},
    {"name": "Catalogue", "keys": [("GET", "/catalogue/<type>"), ("GET", "/catalogue/<type>/<page>"),
                                   ("GET", "/catalogue/<type>/<page>/json"),
                                   ("GET", "/catalogue/<type>/recherche-avancee")]},
    {"name": "Elements", "keys": [("GET", "/catalogue/item/<id>"), ("GET", "/catalogue/item/<id>/data"),
                                  ("GET", "/catalogue/item/<id>/gallery"),
                                  ("GET", "/catalogue/item/<id>/comments/json"),
                                  ("GET", "/catalogue/item/<id>/magnets/download"),
                                  ("GET", "/catalogue/item/<id>/details/json"),
                                  ("GET", "/api/items/<id>/image-status"), ("POST", "/catalogue/item/<id>/rate"),
                                  ("POST", "/catalogue/item/<id>/comment"), ("POST", "/api/catalogue/item/<id>/reply"),
                                  ("POST", "/api/items/<id>/viz-links"), ("POST", "/api/items/<id>/verify"),
                                  ("POST", "/api/items/<id>/unpublish")]},
    {"name": "Utilisateurs", "keys": [("GET", "/profile/<user_id>"), ("GET", "/compte"),
                                      ("GET", "/upload"), ("GET", "/brouillons"),
                                      ("PUT", "/api/users/profile"),
                                      ("POST", "/api/users/change-password"), ("POST", "/api/users/2fa/setup"),
                                      ("POST", "/api/users/2fa/enable"), ("POST", "/api/users/2fa/disable"),
                                      ("POST", "/api/users/generate-recovery-codes"), ("POST", "/api/users/avatar")]},
    {"name": "Publication", "keys": [("POST", "/api/upload/file"), ("POST", "/api/upload/item"),
                                     ("PUT", "/api/upload/item/<id>"), ("DELETE", "/api/upload/item/<id>"),
                                     ("POST", "/api/upload/item/<id>/publish"),
                                     ("POST", "/api/upload/item/<id>/restore"),
                                     ("DELETE", "/api/upload/item/<id>/purge"),
                                     ("GET", "/api/upload/drafts"), ("DELETE", "/api/upload/drafts/all"),
                                     ("POST", "/api/upload/drafts/publish"),
                                     ("GET", "/api/upload/trash"), ("DELETE", "/api/upload/trash/all"),
                                     ("GET", "/api/upload/publications"), ("DELETE", "/api/upload/publications/all"),
                                     ("POST", "/api/upload/publications/verify")]},
    {"name": "Organisations", "keys": [("GET", "/organizations"), ("GET", "/organizations/<page>"),
                                        ("GET", "/organizations/<slug>/items"), ("GET", "/organizations/<slug>"),
                                        ("POST", "/api/organizations"),
                                        ("POST", "/api/organizations/<slug>/join"),
                                        ("GET", "/api/organizations/<slug>/requests"),
                                        ("POST", "/api/organizations/<slug>/requests/<request_id>/approve"),
                                        ("POST", "/api/organizations/<slug>/requests/<request_id>/reject"),
                                        ("POST", "/api/organizations/<slug>/leave"),
                                        ("POST", "/api/organizations/<slug>/members/<user_id>/role"),
                                        ("DELETE", "/api/organizations/<slug>/members/<user_id>"),
                                        ("POST", "/api/organizations/<slug>/invite"),
                                        ("GET", "/api/organizations/<slug>/roles"),
                                        ("POST", "/api/organizations/<slug>/roles"),
                                        ("PUT", "/api/organizations/<slug>/roles/<role_id>"),
                                        ("DELETE", "/api/organizations/<slug>/roles/<role_id>"),
                                        ("DELETE", "/api/organizations/<slug>")]},
    {"name": "Signalements", "keys": [("POST", "/api/reports")]},
    {"name": "Contact", "keys": [("POST", "/api/contact")]},
    {"name": "Pages & documentation", "keys": [("GET", "/changelog"), ("GET", "/feuille-de-route"),
                                               ("GET", "/rapport"), ("GET", "/rapport/pdf/<filename>"),
                                               ("GET", "/docs"), ("GET", "/docs/<slug>"),
                                               ("GET", "/apropos"), ("GET", "/contact"),
                                               ("GET", "/mentions-legales"), ("GET", "/conditions-utilisation"),
                                               ("GET", "/confidentialite"), ("GET", "/health")]},
    {"name": "Administration", "keys": [("GET", "/admin/accueil"), ("GET", "/admin/users"),
                                         ("GET", "/admin/users/<page>"),
                                         ("POST", "/api/users/<id>/ban"),
                                         ("GET", "/api/users/banned"), ("GET", "/admin/reports"),
                                         ("POST", "/api/admin/reports/<id>/resolve"),
                                         ("GET", "/admin/moderation"), ("DELETE", "/api/admin/comments/<id>"),
                                         ("DELETE", "/api/admin/items/<id>"),
                                         ("POST", "/api/admin/items/<id>/verify"),
                                         ("POST", "/api/admin/items/<id>/unverify"),
                                         ("GET", "/admin/audit"), ("GET", "/admin/contact-messages"),
                                         ("GET", "/admin/mirrors"),
                                         ("GET", "/admin/featured"), ("GET", "/admin/geopackages"),
                                         ("GET", "/admin/catalogues"),
                                         ("GET", "/admin/replication"), ("GET", "/admin/tags"),
                                         ("GET", "/admin/settings"), ("GET", "/admin/backup"),
                                         ("GET", "/admin/qbittorrent"), ("GET", "/admin/changelog"),
                                         ("GET", "/api/admin/qbittorrent/status"),
                                         ("POST", "/api/admin/qbittorrent/cleanup"),
                                         ("GET", "/api/admin/simple-files"), ("POST", "/api/admin/simple-files"),
                                         ("PUT", "/api/admin/simple-files/<id>"),
                                         ("DELETE", "/api/admin/simple-files/<id>"),
                                         ("GET", "/api/admin/mirrors"), ("POST", "/api/admin/mirrors"),
                                         ("PUT", "/api/admin/mirrors/<id>"), ("DELETE", "/api/admin/mirrors/<id>"),
                                         ("GET", "/api/admin/featured"), ("POST", "/api/admin/featured"),
                                         ("PUT", "/api/admin/featured/<id>"), ("DELETE", "/api/admin/featured/<id>"),
                                         ("GET", "/api/admin/geopackages"), ("POST", "/api/admin/geopackages"),
                                         ("PUT", "/api/admin/geopackages/<id>"),
                                         ("DELETE", "/api/admin/geopackages/<id>"),
                                         ("GET", "/api/admin/contact-messages"),
                                         ("POST", "/api/admin/contact-messages/<id>/read"),
                                         ("DELETE", "/api/admin/contact-messages/<id>"),
                                         ("GET", "/api/admin/audit"), ("GET", "/api/admin/items"),
                                         ("GET", "/api/admin/items/search"), ("GET", "/api/admin/comments"),
                                         ("GET", "/api/admin/reports"),
                                         ("POST", "/api/admin/catalogues/<catalogue_type>/toggle"),
                                         ("GET", "/api/admin/tags"), ("POST", "/api/admin/tags"),
                                         ("PUT", "/api/admin/tags/<id>"), ("DELETE", "/api/admin/tags/<id>"),
                                         ("POST", "/api/admin/tags/<id>/tags"),
                                         ("PUT", "/api/admin/tags/<id>/tags/<tag_id>"),
                                         ("DELETE", "/api/admin/tags/<id>/tags/<tag_id>"),
                                         ("POST", "/api/admin/settings/update"),
                                         ("POST", "/api/admin/settings/logo-upload"),
                                         ("GET", "/api/admin/backup/download"),
                                         ("POST", "/api/admin/backup/restore"),
                                         ("POST", "/api/admin/replication/preview"),
                                         ("POST", "/api/admin/replication/fetch")], "admin": True},
]


METHOD_COLORS = {
    "GET": "#2d8cff",
    "POST": "#28a745",
    "PUT": "#ffc107",
    "DELETE": "#dc3545",
}

ALLOWED_EXTENSIONS = "csv, shp, geojson, gpkg, json, xml, png, jpg, jpeg, svg, pdf"

def _build_endpoints():
    lookup = {(ep["method"], ep["path"]): ep for ep in _ENDPOINTS}
    result = []
    for cat in CATEGORIES:
        endpoints = []
        for key in cat["keys"]:
            ep = lookup[key]
            body = ep.get("body")
            ep_out = {
                "method": ep["method"],
                "path": ep["path"],
                "desc": ep["desc"],
                "auth": ep["auth"],
                "rate": ep.get("rate"),
                "examples": _examples(
                    ep["method"], ep["path"],
                    body=body,
                    auth=ep["auth"],
                    form=ep.get("form", False),
                    multipart=ep.get("multipart", False),
                ),
            }
            endpoints.append(ep_out)
        entry = {"category": cat["name"], "endpoints": endpoints}
        if cat.get("admin"):
            entry["admin"] = True
        result.append(entry)
    return result


API_ENDPOINTS = _build_endpoints()


@bp.route("/api")
def api_docs_index():
    return render_template(
        "api_docs.html",
        title="A.N.A.N.A.S | API",
        meta_description="Documentation complete de l'API REST d'A.N.A.N.A.S",
        endpoints=API_ENDPOINTS,
        method_colors=METHOD_COLORS,
        allowed_extensions=ALLOWED_EXTENSIONS,
    )