# Reset Docker Containers & Credentials

## Commande pour réinitialiser l'environnement (mode production)

```bash
docker compose down -v && rm -f .env && ./setup.sh
```

Cette commande :
1. Arrête et supprime tous les conteneurs + volumes (`docker compose down -v`)
2. Supprime le fichier `.env` existant avec les anciennes credentials (`rm -f .env`)
3. Recréé un nouveau `.env` et relance les containers (`./setup.sh`)
