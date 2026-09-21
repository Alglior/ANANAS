"""Purge périodique du cache d'images expiré (TTL 30 jours).

Sans purge, le dossier instance/image_cache grandit indéfiniment : le TTL
n'est jusqu'ici vérifié qu'à la réutilisation d'un magnet. Ce script tourne
en continu au démarrage du conteneur et supprime, toutes les quelques heures,
les fichiers expirés qui ne sont plus référencés par aucun item.

Usage (dans un environnement où SQLALCHEMY_DATABASE_URI est joignable) :
    python scripts/cache_sweeper.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

DEFAULT_INTERVAL = int(os.environ.get("CACHE_SWEEPER_INTERVAL", str(6 * 60 * 60)))


def main(interval_seconds=DEFAULT_INTERVAL):
    app = create_app()
    while True:
        try:
            with app.app_context():
                from src.image_cache import purge_expired_cache
                removed = purge_expired_cache()
                if removed:
                    print(f"[sweeper] {removed} fichier(s) de cache expiré(s) purgé(s)")
        except Exception as e:
            print(f"[sweeper] Erreur de purge : {e}", file=sys.stderr)
        time.sleep(max(interval_seconds, 60))


if __name__ == "__main__":
    main()