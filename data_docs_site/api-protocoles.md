# API & Protocoles

La documentation complète de l'API REST est désormais disponible sur une page dédiée :

➡️ **[Documentation API](/api)**

Vous y trouverez la liste complète des endpoints avec leurs méthodes, descriptions, prérequis d'authentification et limites de débit.

---

## Distribution des données

Les données sont distribuées via des **liens magnet** et le protocole **BitTorrent**, garantissant :

- La décentralisation — pas de point de défaillance unique
- La disponibilité — les données restent accessibles tant qu'au moins un pair les partage
- L'intégrité — vérification des fichiers via hachage SHA-1

## Formats supportés

| Type | Description |
|------|-------------|
| Géodonnées | Fichiers SIG, shapefiles, GeoJSON, CSV, GPKG |
| Cartes | Produits cartographiques, tuiles, cartes interactives |
| Applications | Services web, outils géospatiaux |

## Niveaux de format

- **Pack** : archives complètes (zip, tar.gz) via magnet link
- **Individuel** : fichiers unitaires (csv, shp, geojson, gpkg, json, xml, png, jpg, gif, svg, pdf)