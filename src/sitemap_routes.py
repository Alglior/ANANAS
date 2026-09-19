from urllib.parse import quote
from xml.sax.saxutils import escape

from flask import Blueprint, Response, request

bp = Blueprint("sitemap", __name__)


def _abs(path):
    return request.host_url.rstrip("/") + path


@bp.route("/sitemap.xml")
def sitemap_xml():
    from models import Item, Organization
    from src.doc_routes import _list_docs

    urls = []

    def add(path, changefreq="weekly", priority="0.7", lastmod=None):
        urls.append({
            "loc": _abs(path),
            "changefreq": changefreq,
            "priority": priority,
            "lastmod": lastmod,
        })

    add("/", changefreq="daily", priority="1.0")
    add("/catalogue", priority="0.9")
    add("/catalogue/donnees", priority="0.9")
    add("/catalogue/cartes", priority="0.9")
    add("/catalogue/applications", priority="0.9")
    add("/catalogue/donnees/recherche-avancee")
    add("/catalogue/cartes/recherche-avancee")
    add("/catalogue/applications/recherche-avancee")
    add("/organizations")
    add("/apropos")
    add("/contact")
    add("/confidentialite")
    add("/conditions-utilisation")
    add("/mentions-legales")
    add("/feuille-de-route")
    add("/changelog")
    add("/rapport")
    add("/docs")

    for doc in _list_docs():
        add(f"/docs/{quote(doc['slug'])}")

    for item in Item.query.filter_by(status="published").order_by(Item.id).all():
        lastmod = item.created_at.strftime("%Y-%m-%d") if item.created_at else None
        add(f"/catalogue/item/{item.id}", changefreq="monthly", priority="0.8", lastmod=lastmod)

    for org in Organization.query.filter_by(is_active=True).order_by(Organization.id).all():
        add(f"/organizations/{quote(org.slug)}", priority="0.6")
        add(f"/organizations/{quote(org.slug)}/items", priority="0.6")

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        parts.append("<url>")
        parts.append(f"<loc>{escape(u['loc'])}</loc>")
        if u["lastmod"]:
            parts.append(f"<lastmod>{u['lastmod']}</lastmod>")
        parts.append(f"<changefreq>{u['changefreq']}</changefreq>")
        parts.append(f"<priority>{u['priority']}</priority>")
        parts.append("</url>")
    parts.append("</urlset>")

    return Response("\n".join(parts), mimetype="application/xml")