#!/usr/bin/env python3
"""Recalcule et persiste le score IMOD pour tous les items.

À exécuter après le déploiement de la migration ajoutant la colonne
imod_score, ou périodiquement pour réparer des scores obsolètes.
"""
import sys

sys.path.insert(0, ".")

from app import create_app, db
from models import Item


def main():
    app = create_app()
    with app.app_context():
        items = Item.query.all()
        for idx, item in enumerate(items, start=1):
            item.refresh_imod_cache()
            if idx % 50 == 0:
                print(f"[{idx}/{len(items)}] committed...")
                db.session.commit()
        db.session.commit()
        print(f"Done: {len(items)} items refreshed.")


if __name__ == "__main__":
    main()