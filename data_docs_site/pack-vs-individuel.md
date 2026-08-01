# Simple, Pack (GeoPackage) vs Individuel

> **Le lien magnet est obligatoire pour tous les items du catalogue**, quel que soit le niveau de format. Aucune donnée n'est stockée sur le serveur d'A.N.A.N.A.S. — la plateforme ne fait qu'indexer et référencer les données disponibles sur le réseau BitTorrent.

Les données du catalogue sont organisées en trois niveaux de format, définis par le champ `data_format_level` dans le modèle `Item` :

---

## Simple (fichier unique, une seule couche)

Les fichiers **simples** sont des fichiers unitaires contenant une seule couche de données. Distribués exclusivement via **magnet link**.

- **Usage** : Idéal pour un fichier unique sans organisation multi-couche (ex: un CSV, un GeoJSON simple, un shapefile)
- **Distribution** : Magnet link uniquement

---

## Packs (GeoPackage multi-couches)

Les **packs** sont des fichiers uniques au format **GeoPackage** (.gpkg) contenant plusieurs couches de données organisées par thématique. Distribués exclusivement via **magnet link**.

- **Format** : `.gpkg` (standard OGC, base de données SQLite)
- **Usage** : Idéal pour les collections thématiques complètes (ex: un projet SIG avec plusieurs couches, métadonnées intégrées, styles QML pré-configurés)
- **Avantages** :
  - Fichier unique contenant toutes les couches
  - Métadonnées intégrées (descriptions, sources, historique)
  - Styles QML inclus avec alias de variables lisibles
  - Compatible avec tous les logiciels SIG modernes (QGIS, ArcGIS, etc.)
- **Distribution** : Magnet link uniquement (pas d'upload direct sur le serveur)

---

## Individuels (fichiers unitaires multiples)

Les fichiers **individuels** sont des fichiers unitaires distribués **obligatoirement via magnet link**. L'interface d'upload permet uniquement d'ajouter des données de prévisualisation (CSV d'aperçu, galerie d'images) — les données réelles transitent exclusivement par le réseau P2P.

- **Formats supportés** : `.csv`, `.shp`, `.geojson`, `.gpkg`, `.json`, `.xml`, `.png`, `.jpg`, `.gif`, `.svg`, `.pdf`

---

## Tableau comparatif

| Critère | Simple | Pack (GeoPackage) | Individuel |
|---------|--------|-------------------|------------|
| Contenu | Une seule couche dans un fichier | Multi-couches dans un fichier unique `.gpkg` | Plusieurs fichiers unitaires |
| Distribution | Magnet link uniquement | Magnet link uniquement | Magnet link obligatoire |
| Taille typique | Variable (Ko à Mo) | Volumineux (Mo à Go) | Variable (Ko à Mo) |
| Cas d'usage | Fichier cartographique unitaire | Collection thématique SIG complète | Ensemble de fichiers distincts |