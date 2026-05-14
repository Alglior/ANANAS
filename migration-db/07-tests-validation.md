# Phase 7 — Tests & Validation

> **Statut : ✅ TERMININÉ** — Test files existants avec référence explicite "Phase 7" dans les titres.

### 7.1 Fichiers de tests créés
- `tests/test_routes.py` — Tests des routes Flask, organisés par sous-phases (7.1 à 7.6)
- `tests/test_models.py` — Titre : "Phase 7 — Validation des modeles ORM". Vérifie les défauts des modèles (verification_status, upload_status, report status)

### 7.2 Routes testées
| Route | Test attendu |
|-------|-------------|
| `/` | Page index charge sans erreur |
| `/catalogue/donnees` | Affiche les items depuis DB (vérifier count) |
| `/catalogue/cartes` | Idem pour cartes |
| `/catalogue/applications` | Idem pour applications |
| `/catalogue/item/1` | Détail d'un item existant |
| `/catalogue/item/99999` | Redirect vers catalogue (404 implicite) |
| `/catalogue/item/1/gallery` | Galerie affiche les images de DB |

### 7.3 Pagination testée
- Page 1 : items 1-30
- Page 7 : items 181-200 (dernière page donnees)
- Page > total : redirect vers page 1
