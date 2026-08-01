from flask import render_template, redirect, url_for
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


@bp.route("/admin/replication")
@login_required
@require_admin
def admin_replication():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/backup")
@login_required
@require_admin
def admin_backup():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/tags")
@login_required
@require_admin
def admin_tags():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/accueil")
@login_required
@require_admin
def admin_home():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/catalogues")
@login_required
@require_admin
def admin_catalogues():
    return redirect(url_for("admin.admin_settings"))