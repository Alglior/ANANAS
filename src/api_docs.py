from flask import Blueprint, render_template

bp = Blueprint("api_docs", __name__)

BASE = "https://ananas.example.com"


def _examples(method, path, body=None, auth=False):
    """Generate code examples for a given method/path."""
    url = BASE + path
    curl_headers = []
    py_headers = {}
    js_headers = {}

    if auth:
        curl_headers.append('-H "X-CSRF-Token: <token>"')
        py_headers["X-CSRF-Token"] = "<token>"
        js_headers["X-CSRF-Token"] = "<token>"

    has_body = body or method in ("POST", "PUT")
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
     "body": '{"pseudo": "john-doe#ab7f3c", "password": "********"}'},
    {"method": "POST", "path": "/inscription", "desc": "Creer un compte (prenom, nom, mot de passe)", "auth": False, "rate": "3/h",
     "body": '{"prenom": "John", "nom": "Doe", "password": "Str0ng!Pass"}'},
    {"method": "GET",  "path": "/logout", "desc": "Deconnecter et detruire la session", "auth": True, "rate": None},
    {"method": "GET", "path": "/catalogue/<type>", "desc": "Catalogue pagine (types: donnees, cartes, applications)", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/<type>/<page>", "desc": "Page specifique du catalogue", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/<type>/<page>/json", "desc": "Catalogue au format JSON", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>", "desc": "Page de detail d'un element", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/data", "desc": "Onglet donnees (geodonnees uniquement)", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/gallery", "desc": "Onglet galerie / reutilisation", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/comments/json", "desc": "Commentaires pagines (JSON)", "auth": False, "rate": None},
    {"method": "GET", "path": "/catalogue/item/<id>/details/json", "desc": "Details complets (liens de visualisation, chunks)", "auth": False, "rate": None},
    {"method": "GET", "path": "/api/items/<id>/image-status", "desc": "Statut de telechargement des images", "auth": False, "rate": None},
    {"method": "POST", "path": "/catalogue/item/<id>/rate", "desc": "Noter un element (1-5 etoiles)", "auth": True, "rate": None,
     "body": '{"rating": 4}'},
    {"method": "POST", "path": "/catalogue/item/<id>/comment", "desc": "Ajouter un commentaire", "auth": True, "rate": None,
     "body": '{"content": "Tres utile, merci !"}'},
    {"method": "POST", "path": "/api/catalogue/item/<id>/reply", "desc": "Repondre a un commentaire", "auth": True, "rate": None,
     "body": '{"content": "Je confirme !", "parent_id": 42}'},
    {"method": "POST", "path": "/api/items/<id>/viz-links", "desc": "Ajouter un lien de visualisation", "auth": True, "rate": None,
     "body": '{"name": "Carte interactive", "url": "https://...", "link_type": "external"}'},
    {"method": "GET",  "path": "/profile/<user_id>", "desc": "Profil public d'un utilisateur", "auth": False, "rate": None},
    {"method": "GET",  "path": "/compte", "desc": "Tableau de bord (infos, securite, activite)", "auth": True, "rate": None},
    {"method": "PUT",  "path": "/api/users/profile", "desc": "Modifier son prenom / nom", "auth": True, "rate": None,
     "body": '{"prenom": "Jean", "nom": "Dupont"}'},
    {"method": "POST", "path": "/api/users/change-password", "desc": "Changer son mot de passe", "auth": True, "rate": "5/h",
     "body": '{"current_password": "OldPass1!", "new_password": "NewStr0ng!"}'},
    {"method": "POST", "path": "/api/users/avatar", "desc": "Uploader un avatar (png/jpg/webp)", "auth": True, "rate": None,
     "body": '<fichier> (multipart/form-data)'},
    {"method": "POST", "path": "/api/upload/file", "desc": "Uploader un fichier", "auth": True, "rate": None,
     "body": '<fichier> (multipart/form-data)'},
    {"method": "POST", "path": "/api/upload/item", "desc": "Creer un element", "auth": True, "rate": None,
     "body": '{"title": "Ma donnee", "type": "geodonnee", "description": "...", "magnet_link": "magnet:?...", "format_type": "GeoJSON"}'},
    {"method": "PUT",  "path": "/api/upload/item/<id>", "desc": "Modifier un brouillon", "auth": True, "rate": None,
     "body": '{"title": "Titre mis a jour", "description": "..."}'},
    {"method": "DELETE", "path": "/api/upload/item/<id>", "desc": "Mettre a la corbeille", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/upload/item/<id>/restore", "desc": "Restaurer depuis la corbeille", "auth": True, "rate": None},
    {"method": "DELETE", "path": "/api/upload/item/<id>/purge", "desc": "Supprimer definitivement", "auth": True, "rate": None},
    {"method": "GET",  "path": "/api/upload/drafts", "desc": "Brouillons (pagine)", "auth": True, "rate": None},
    {"method": "GET",  "path": "/api/upload/trash", "desc": "Corbeille (pagine)", "auth": True, "rate": None},
    {"method": "GET",  "path": "/api/upload/publications", "desc": "Publications (pagine)", "auth": True, "rate": None},
    {"method": "GET",    "path": "/organizations", "desc": "Liste des organisations", "auth": False, "rate": None},
    {"method": "GET",    "path": "/organizations/<slug>", "desc": "Detail d'une organisation", "auth": False, "rate": None},
    {"method": "POST",   "path": "/api/organizations", "desc": "Creer une organisation", "auth": True, "rate": None,
     "body": '{"name": "Ma Super Organisation", "slug": "ma-super-org", "description": "..."}'},
    {"method": "POST",   "path": "/api/organizations/<slug>/join", "desc": "Rejoindre une organisation", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/leave", "desc": "Quitter une organisation", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/members/<user_id>/role", "desc": "Modifier le role d'un membre", "auth": True, "rate": None,
     "body": '{"role": "editor"}'},
    {"method": "DELETE", "path": "/api/organizations/<slug>/members/<user_id>", "desc": "Retirer un membre", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/invite", "desc": "Inviter un membre par email", "auth": True, "rate": None,
     "body": '{"email": "user@example.com"}'},
    {"method": "GET",    "path": "/api/organizations/<slug>/roles", "desc": "Lister les roles personnalises", "auth": True, "rate": None},
    {"method": "POST",   "path": "/api/organizations/<slug>/roles", "desc": "Creer un role personnalise", "auth": True, "rate": None,
     "body": '{"name": "Editeur", "permissions": ["manage_items"]}'},
    {"method": "PUT",    "path": "/api/organizations/<slug>/roles/<role_id>", "desc": "Modifier un role", "auth": True, "rate": None,
     "body": '{"name": "Super Editeur", "permissions": ["manage_items", "invite_members"]}'},
    {"method": "DELETE", "path": "/api/organizations/<slug>/roles/<role_id>", "desc": "Supprimer un role", "auth": True, "rate": None},
    {"method": "DELETE", "path": "/api/organizations/<slug>", "desc": "Supprimer l'organisation", "auth": True, "rate": None},
    {"method": "POST", "path": "/api/reports", "desc": "Signaler un contenu (spam, fausses donnees, autre)", "auth": True, "rate": None,
     "body": '{"report_type": "item_geodonnee", "target_item_id": 42, "reason": "fake_data", "description": "..."}'},
    {"method": "POST", "path": "/api/contact", "desc": "Envoyer un message de contact", "auth": False, "rate": "5/h",
     "body": '{"name": "Jean", "email": "jean@example.com", "subject": "Question", "message": "Bonjour, ..."}'},
    {"method": "GET",    "path": "/admin/accueil", "desc": "Tableau de bord administrateur", "auth": True, "rate": None, "admin": True},
    {"method": "GET",    "path": "/admin/users", "desc": "Gestion des utilisateurs", "auth": True, "rate": None, "admin": True},
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
]


CATEGORIES = [
    {"name": "Authentification", "keys": ["/connexion", "/inscription", "/logout"]},
    {"name": "Catalogue", "keys": ["/catalogue/<type>", "/catalogue/<type>/<page>", "/catalogue/<type>/<page>/json"]},
    {"name": "Elements", "keys": ["/catalogue/item/<id>", "/catalogue/item/<id>/data", "/catalogue/item/<id>/gallery",
                                   "/catalogue/item/<id>/comments/json", "/catalogue/item/<id>/details/json",
                                   "/api/items/<id>/image-status", "/catalogue/item/<id>/rate",
                                   "/catalogue/item/<id>/comment", "/api/catalogue/item/<id>/reply",
                                   "/api/items/<id>/viz-links"]},
    {"name": "Utilisateurs", "keys": ["/profile/<user_id>", "/compte", "/api/users/profile",
                                       "/api/users/change-password", "/api/users/avatar"]},
    {"name": "Publication", "keys": ["/api/upload/file", "/api/upload/item", "/api/upload/item/<id>",
                                      "/api/upload/item/<id>/restore", "/api/upload/item/<id>/purge",
                                      "/api/upload/drafts", "/api/upload/trash", "/api/upload/publications"]},
    {"name": "Organisations", "keys": ["/organizations", "/organizations/<slug>", "/api/organizations",
                                        "/api/organizations/<slug>/join", "/api/organizations/<slug>/leave",
                                        "/api/organizations/<slug>/members/<user_id>/role",
                                        "/api/organizations/<slug>/members/<user_id>",
                                        "/api/organizations/<slug>/invite", "/api/organizations/<slug>/roles",
                                        "/api/organizations/<slug>/roles/<role_id>",
                                        "/api/organizations/<slug>"]},
    {"name": "Signalements", "keys": ["/api/reports"]},
    {"name": "Contact", "keys": ["/api/contact"]},
    {"name": "Administration", "keys": ["/admin/accueil", "/admin/users", "/api/users/<id>/ban",
                                         "/api/users/banned", "/admin/reports", "/api/admin/reports/<id>/resolve",
                                         "/admin/moderation", "/api/admin/comments/<id>", "/api/admin/items/<id>",
                                         "/api/admin/items/<id>/verify", "/api/admin/items/<id>/unverify",
                                         "/admin/audit", "/admin/contact-messages", "/admin/mirrors",
                                         "/admin/featured", "/admin/geopackages", "/admin/catalogues",
                                         "/admin/replication", "/admin/tags"], "admin": True},
]


METHOD_COLORS = {
    "GET": "#2d8cff",
    "POST": "#28a745",
    "PUT": "#ffc107",
    "DELETE": "#dc3545",
}

ALLOWED_EXTENSIONS = "csv, shp, geojson, gpkg, json, xml, png, jpg, gif, svg, pdf"


def _build_endpoints():
    lookup = {ep["path"]: ep for ep in _ENDPOINTS}
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
                "examples": _examples(ep["method"], ep["path"], body=body, auth=ep["auth"]),
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