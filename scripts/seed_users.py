import os
import sys

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

def generate_fake_users(n=100):
    from werkzeug.security import generate_password_hash
    users = []
    for i in range(1, n + 1):
        prenom = PRENOMS[i % len(PRENOMS)]
        nom = NOMS[i % len(NOMS)]
        email = f"{prenom.lower()}.{nom.lower().replace(' ', '')}@fake{str(i).zfill(3)}.ma"

        is_active = i % 12 != 0
        banned = i % 50 == 0 and i > 50

        password = generate_password_hash(f"password{i}")

        user = User(
            prenom=prenom,
            nom=nom,
            email=email,
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
