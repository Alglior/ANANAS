# Phase 5 — Refactorisation de `app.py` (Remplacement du Mock par DB)

### 5.1 Remplacer `get_catalogue_page()`
**Fichier :** `app.py`, lignes 214-229 → supprimées et remplacées par :

```python
def get_catalogue_page(total_page=1, per_page=ITEMS_PER_PAGE, catalogue="donnees", filter_verified=False, org_slug=None):
    type_map = {
        "donnees": "geodonnee",
        "cartes": "carte",
        "applications": "application"
    }
    item_type = type_map[catalogue]

    query = Item.query.filter_by(type=item_type)
    if org_slug:
        # Filtrer par slug d'organisation (items publiés par une orga spécifique)
        org = Organization.query.filter_by(slug=org_slug).first()
        if org:
            query = query.filter_by(organization_id=org.id)
    if filter_verified:
        query = query.filter_by(verification_status="verified")  # seulement données de confiance officielle
    else:
        query = query.all()  # toutes les données visibles (pending + verified, pas de filtrage par défaut)
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page

    if total_page > total_pages or total_page < 1:
        return None

    items = query.offset((total_page - 1) * per_page).limit(per_page).all()

    # Convertir les modèles ORM en dicts (compatibilité templates)
    result_items = [item.to_dict() for item in items]
    page_numbers = _build_page_numbers(total_page, total_pages)

    return {
        "items": result_items,
        "page": total_page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }
```

### 5.2 Ajouter la méthode `to_dict()` sur le modèle `Item`
**Fichier :** `models.py`

```python
def to_dict(self):
    """Convertit l'item ORM en dict compatible avec les templates Jinja."""
    return {
        "id": self.id,
        "title": self.title,
        "description": self.description,
        "format": self.format_type,
        "size": f"{self.size_mb} Mo" if self.size_mb else "",
        "magnet": self.magnet_link,
        "image": self.image_path,
        "author": self.author_name,
        "organization_id": self.organization_id,
        "organization_name": self.organization.name if self.organization else None,
        "organization_slug": self.organization.slug if self.organization else None,
        "created_at": self.created_at.strftime("%Y-%m-%d"),
        "tags": [t.tag for t in self.tags],
        "gallery": self._build_gallery_dict(),
        "pdf_doc": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/r6.pdf",
        # ─── Vérification de confiance (ajouté) — ne signifie PAS modération ───
        "verification_status": self.verification_status,
        "is_official_verified": self.verification_status == "verified",
        "verifier_nom": f"{self.verifier.prenom} {self.verifier.nom}" if self.verifier else None,
        "verified_at": self.verified_at.strftime("%Y-%m-%d") if self.verified_at else None,
        "verification_notes": self.verification_notes,
    }

def _build_gallery_dict(self):
    result = []
    for g in self.gallery_items:
        entry = {"type": g.media_type, "label": g.label}
        if g.src:
            entry["src"] = g.src
        if g.data_json:
            if g.media_type == "csv":
                entry["data"] = g.data_json.get("rows", [])
            elif g.media_type == "dashboard":
                entry["metrics"] = g.data_json.get("metrics", [])
        result.append(entry)
    return result
```

### 5.3 Remplacer `item_detail_view()`
**Fichier :** `app.py`, lignes 409-435 → remplacées par :

```python
def item_detail_view(item_id):
    item = Item.query.get_or_404(item_id)
    related_items = Item.query.filter(
        Item.format_type == item.format_type,
        Item.id != item_id,
        Item.is_published == True
    ).limit(3).all()

    img_gallery = [g for g in item.gallery_items if g.media_type == "image"]

    return render_template(
        "item_detail.html",
        title=f"A.N.A.N.A.S. | {item.title}",
        meta_description=item.description[:160],
        item=item.to_dict(),
        related_items=[ri.to_dict() for ri in related_items],
        image_gallery=img_gallery,
    )
```

### 5.4 Remplacer `item_gallery_view()`
**Fichier :** `app.py`, lignes 440-456 → remplacées par :

```python
def item_gallery_view(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template(
        "gallery.html",
        title=f"Galerie — {item.title}",
        meta_description="Galerie de " + item.title,
        item=item.to_dict(),
    )
```

### 5.5 Supprimer le code mock du module-level
**Fichier :** `app.py`

Supprimer entièrement :
- Lignes 8-211 : toutes les constantes et générateurs mock (`_CATALOGUE_ITEMS`, `LOREM_IPSUM_FR`, `_build_gallery_item`, etc.)
- Ligne 207-211 : `_ALL_CATALOGUES`
- Lignes 232-252 : `_build_page_numbers` → déplacer dans `models.py` ou garder si réutilisé

### 5.6 Mettre à jour `catalogue_view()`
**Fichier :** `app.py`, lignes 375-390

Remplacer la référence `_ALL_CATALOGUES` par le mapping direct :
```python
def catalogue_view(catalogue="donnees", page=1):
    type_map = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}
    if catalogue not in type_map:
        return redirect(url_for("catalogue"))

    meta = _CATALOGUE_META[catalogue]
    data = get_catalogue_page(page, catalogue=catalogue)
    ...
```
