from flask import render_template
from src.admin import bp, login_required, require_admin, get_catalogues_status, _CATALOGUES_INFO


@bp.route("/admin/reports")
@login_required
@require_admin
def admin_reports():
    return render_template("admin/reports.html", title="Administration — Signalements", meta_description="Liste des signalements")


@bp.route("/admin/moderation")
@login_required
@require_admin
def admin_moderation():
    return render_template("admin/moderation.html", title="Administration — Modération", meta_description="Modération des contenus et commentaires")


@bp.route("/admin/audit")
@login_required
@require_admin
def admin_audit():
    return render_template("admin/audit.html", title="Administration — Journal d'audits", meta_description="Journal des actions administratives")


@bp.route("/admin/contact-messages")
@login_required
@require_admin
def admin_contact_messages():
    return render_template("admin/contact_messages.html", title="Administration — Messages de contact", meta_description="Messages reçus via la page contact")


@bp.route("/admin/mirrors")
@login_required
@require_admin
def admin_mirrors():
    return render_template("admin/mirrors.html", title="Administration — Sites miroirs", meta_description="Gestion des sites miroirs")


@bp.route("/admin/featured")
@login_required
@require_admin
def admin_featured():
    return render_template("admin/featured.html", title="Administration — Données en avant", meta_description="Gestion des données mises en avant")


@bp.route("/admin/geopackages")
@login_required
@require_admin
def admin_geopackages():
    return render_template("admin/geopackages.html", title="Administration — GeoPackages", meta_description="Gestion des packs GeoPackage")


@bp.route("/admin/catalogues")
@login_required
@require_admin
def admin_catalogues():
    status = get_catalogues_status()
    catalogues = [{"type": info["type"], "label": info["label"], "active": status.get(info["type"], True)} for info in _CATALOGUES_INFO]
    return render_template("admin/catalogues.html", title="Administration — Catalogues", meta_description="Activer ou désactiver les catalogues", catalogues=catalogues)


@bp.route("/admin/replication")
@login_required
@require_admin
def admin_replication():
    return render_template("admin/replication.html", title="Administration — Réplication", meta_description="Répliquer des catalogues depuis une instance distante")


@bp.route("/admin/tags")
@login_required
@require_admin
def admin_tags():
    return render_template("admin/tags.html", title="Administration — Étiquettes", meta_description="Gestion des catégories d'étiquettes et étiquettes")

@bp.route("/admin/accueil")
@login_required
@require_admin
def admin_home():
    return render_template("admin/home.html", title="Administration — Accueil", meta_description="Gestion de la page d'accueil")