from flask import Blueprint, render_template
from models import MirrorSite, FeaturedItem, GeoPackage

bp = Blueprint("index", __name__)


@bp.route("/")
def home():
    mirrors = MirrorSite.query.filter_by(is_active=True).order_by(MirrorSite.display_order, MirrorSite.id).all()
    featured = FeaturedItem.query.filter_by(is_active=True).order_by(FeaturedItem.display_order, FeaturedItem.id).all()
    geo_packages = GeoPackage.query.filter_by(is_active=True).order_by(GeoPackage.display_order, GeoPackage.id).all()
    return render_template(
        "index.html",
        title="A.N.A.N.A.S | Accueil",
        meta_description="Portail géoservices basé sur des liens magnet et torrents.",
        mirrors=mirrors,
        featured_items=featured,
        geo_packages=geo_packages,
    )