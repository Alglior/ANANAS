"""Relance les téléchargements d'images magnet interrompus.

Après un arrêt brutal (crash, redémarrage du conteneur), les jobs d'images
restent bloqués en statut "pending" / "downloading" / "saving" / "failed" :
les threads qui attendaient la fin du téléchargement sont morts. Ce script
ré-injecte ces items dans le ThreadPoolExecutor de l'app, au démarrage du
conteneur, et nettoie les items restés "en cours" sans rien à télécharger.

Usage (dans un environnement où SQLALCHEMY_DATABASE_URI est joignable) :
    python scripts/resume_image_downloads.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


def resume():
    app = create_app()
    with app.app_context():
        from src.user_routes import relaunch_unfinished_image_jobs
        relaunched, cleaned = relaunch_unfinished_image_jobs()

    print(
        f"[resume] {relaunched} item(s) relancé(s)"
        + (f", {cleaned} item(s) au statut 'en cours' corrigé(s)" if cleaned else "")
    )
    return relaunched


if __name__ == "__main__":
    resume()