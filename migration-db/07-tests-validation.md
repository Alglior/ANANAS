# Phase 7 — Tests & Validation

### 7.1 Vérifier chaque route

| Route | Test attendu |
|-------|-------------|
| `/` | Page index charge sans erreur |
| `/catalogue/donnees` | Affiche les items depuis DB (vérifier count) |
| `/catalogue/cartes` | Idem pour cartes |
| `/catalogue/applications` | Idem pour applications |
| `/catalogue/item/1` | Détail d'un item existant |
| `/catalogue/item/99999` | Redirect vers catalogue (404 implicite) |
| `/catalogue/item/1/gallery` | Galerie affiche les images de DB |

### 7.2 Vérifier la pagination

- Page 1 : items 1-30
- Page 7 : items 181-200 (dernière page donnees)
- Page > total : redirect vers page 1
