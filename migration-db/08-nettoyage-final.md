# Phase 8 — Nettoyage Final

### 8.1 Supprimer les imports/mock restants dans `app.py`
- `import hashlib` → supprimer si non utilisé ailleurs
- `ITEMS_PER_PAGE` → garder mais déplacer en constante de config

### 8.2 Mettre à jour `.gitignore`
```
# .env (déjà présent)
# __pycache__/ (déjà présent)
*.pyc

# Ajouts possibles :
.mypy_cache/
.pytest_cache/
```

### 8.3 Vérifier Dockerfile
S'assurer que `requirements.txt` est rebuild avec les nouvelles deps :
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```
