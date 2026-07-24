from flask import Blueprint, render_template
from models import MirrorSite, FeaturedItem

bp = Blueprint("index", __name__)


@bp.route("/")
def home():
    mirrors = MirrorSite.query.filter_by(is_active=True).order_by(MirrorSite.display_order, MirrorSite.id).all()
    featured = FeaturedItem.query.filter_by(is_active=True).order_by(FeaturedItem.display_order, FeaturedItem.id).all()
    return render_template(
        "index.html",
        title="A.N.A.N.A.S. | Accueil",
        meta_description="Portail géoservices basé sur des liens magnet et torrents.",
        mirrors=mirrors,
        featured_items=featured,
    )