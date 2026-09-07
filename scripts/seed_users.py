import os
import sys
import random
import string
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from models import User


PRENOMS = [
    "Lucas", "Liam", "Arthur", "Louis", "Gabriel", "Romain", "Mathis", "Jules",
    "Hugo", "Léa", "Manon", "Chloé", "Emma", "Mila", "Alice", "Rose",
    "Clara", "Jade", "Inès", "Louise", "Camille", "Léna", "Sarah", "Anna",
    "Noah", "Thomas", "Antoine", "Nicolas", "Pierre", "Philippe", "François",
    "Jean", "Jacques", "Michel", "Bernard", "Daniel", "Sébastien", "Maxime",
    "Alexandre", "Paul", "Adam", "Nathan", "Ethan", "Isaac", "Jade", "Juliette",
    "Zoé", "Célia", "Margaux", "Victoire", "Astrid", "Nora", "Lina", "Romane",
]

NOMS = [
    "Dubois", "Thierry", "Moreau", "Fournier", "Girard", "Bernard", "Rousseau",
    "Leroy", "Roux", "Faure", "Petit", "Durand", "Legrand", "Muller", "Schmidt",
    "Boucher", "Mercier", "Perrin", "Monnier", "Martin", "Roche", "Galland",
    "Chevalier", "Bonnet", "Dupont", "Laurent", "Lefevre", "Simon", "Blanc",
    "Guerin", "Drain", "Lecomte", "Delacroix", "Deschamps", "Montagud", "Benoit",
    "Lambert", "Fontaine", "Ferrand", "Hebert", "Nicolas", "Poirier", "Morel",
    "Picard", "Henry", "Carlier", "Bossant", "Clément", "Garnier", "Colson",
]

def _normalize(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


def generate_fake_users(n=100):
    from werkzeug.security import generate_password_hash
    users = []
    existing_pseudos = set()
    for i in range(1, n + 1):
        prenom = PRENOMS[i % len(PRENOMS)]
        nom = NOMS[i % len(NOMS)]

        is_active = i % 12 != 0
        banned = i % 50 == 0 and i > 50

        password = generate_password_hash(f"password{i}")

        base = f"{_normalize(prenom).lower()}-{_normalize(nom).lower().replace(' ', '-')}"
        while True:
            letters = ''.join(random.choices(string.ascii_lowercase, k=2))
            digits = ''.join(random.choices(string.digits, k=4))
            pseudo = f"{base}#{letters}{digits}"
            if pseudo not in existing_pseudos:
                existing_pseudos.add(pseudo)
                break

        user = User(
            prenom=prenom,
            nom=nom,
            pseudo=pseudo,
            password_hash=password,
            is_active=is_active,
            banned=banned,
            is_admin=False,
        )
        users.append(user)

    return users


def main():
    app = create_app()
    with app.app_context():
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
        existing_count = User.query.count()
        if existing_count >= n:
            print(f"Already have {existing_count} users. Skipping.")
            return

        to_add = generate_fake_users(n)
        db.session.add_all(to_add)
        try:
            db.session.commit()
            added = len([u for u in to_add if u.id is not None])
            print(f"Added {added} fake users (total: {User.query.count()})")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding users: {e}")


if __name__ == "__main__":
    main()
