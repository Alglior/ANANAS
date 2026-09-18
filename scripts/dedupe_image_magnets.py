"""Nettoie les doublons de galerie/jobs d'images magnet (réplication).

Un même lien magnet ne doit produire qu'une seule image en galerie et un seul
ItemImageJob. Ce script supprime les doublons (ItemGallery + ItemImageJob)
au niveau base, en conservant l'entrée référencée par item.image_path lorsqu'elle
existe, sinon la première.

Usage (dans un environnement où SQLALCHEMY_DATABASE_URI est joignable) :
    python scripts/dedupe_image_magnets.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Item, ItemGallery, ItemImageJob


def dedupe():
    app = create_app()
    deleted_gallery = 0
    deleted_jobs = 0
    fixed_items = set()

    with app.app_context():
        items = Item.query.all()
        for item in items:
            # Galerie : garde une seule entrée image par magnet_link.
            seen = {}
            for g in item.gallery_items:
                if g.media_type != "image" or not isinstance(g.data_json, dict):
                    continue
                magnet = (g.data_json.get("magnet_link") or "").strip()
                if not magnet:
                    continue
                if magnet in seen:
                    db.session.delete(g)
                    deleted_gallery += 1
                    fixed_items.add(item.id)
                else:
                    seen[magnet] = g

            # Jobs : garde un seul job par magnet_link.
            seen_jobs = set()
            for job in item.image_jobs:
                magnet = (job.magnet_link or "").strip()
                if magnet in seen_jobs:
                    db.session.delete(job)
                    deleted_jobs += 1
                else:
                    seen_jobs.add(magnet)

        db.session.commit()

        # Corrige image_magnets_total / image_magnets_pending des items touchés.
        for item_id in fixed_items:
            item = Item.query.get(item_id)
            if item:
                item.image_magnets_total = len(item.image_jobs)
                item.image_magnets_pending = bool(item.image_jobs and any(j.status not in ("done", "failed") for j in item.image_jobs))
        db.session.commit()

    print(f"Galerie : {deleted_gallery} doublon(s) supprimé(s), {len(fixed_items)} item(s) touché(s).")
    print(f"Jobs : {deleted_jobs} doublon(s) supprimé(s).")


if __name__ == "__main__":
    dedupe()