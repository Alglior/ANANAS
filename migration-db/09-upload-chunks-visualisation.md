# Phase 9 — Upload de Chunks & Liens de Visualisation

### 9.1 Endpoint : Upload d'un fragment de données (`/api/upload/chunk`)

Un utilisateur upload une partie des données → elle apparaît dans l'onglet "Données".

**Flux :**
1. L'utilisateur envoie un fichier (POST multipart/form-data à `/api/upload/chunk`) avec :
   - `file` — le dataset fragmenté (CSV, Shapefile, GeoJSON…)
   - `parent_item_id` — optionnel, si rattaché à un item existant
   - `chunk_name` — nom du fragment ("Couche hydrologique Secteur X")

2. Le backend :
   - Crée une entrée dans `user_uploads` avec status `"queued"`
   - Crée un `DataChunk` associé avec status `"pending"`
   - Stocke le fichier (local `/uploads/` ou S3)
   - Lance un worker asynchrone (RQ/Celery) qui :
     a. Convertit/valide le format → statut `"processing"`
     b. Génère les métadonnées + magnet link
     c. Publie le chunk → `is_published=True`, `upload_status="published"`
     d. Si `parent_item_id` est NULL → crée un nouvel `Item` dans le catalogue

3. Le chunk publié apparaît **immédiatement** dans `/catalogue/donnees` (recherche automatique)

```python
@app.route("/api/upload/chunk", methods=["POST"])
@login_required
def upload_chunk():
    file = request.files["file"]
    parent_item_id = request.form.get("parent_item_id")
    chunk_name = request.form["chunk_name"]

    upload = UserUpload(
        owner_user_id=current_user.id,
        parent_item_id=parent_item_id,
        file_name=file.filename,
        file_size_bytes=len(file.read()),
        mime_type=file.content_type,
        original_format=Path(file.filename).suffix.lstrip(".")
    )
    db.session.add(upload)
    db.session.commit()

    chunk = DataChunk(
        parent_item_id=parent_item_id,
        name=chunk_name,
        owner_user_id=current_user.id,
        upload_status="pending",
        data_url=f"/uploads/{upload.id}/{file.filename}",
        metadata_json={"original_file": file.filename}
    )
    db.session.add(chunk)
    db.session.commit()

    upload.chunk_id = chunk.id
    db.session.commit()

    # Déclencher le worker de traitement
    process_chunk_job.delay(upload.id)

    return jsonify({"status": "queued", "upload_id": upload.id})
```

### 9.2 Endpoint : Ajout d'un lien de visualisation (`/api/items/<id>/viz-links`)

Un utilisateur ajoute un lien vers une application externe → il apparaît dans l'onglet "Visualisation" de l'item.

**Flux :**
1. POST à `/api/items/{item_id}/viz-links` avec :
   - `name` — nom affiché ("QGIS Cloud Viewer")
   - `url` — URL cible
   - `link_type` — `"external"` (nouvel onglet), `"embed"` (iframe), `"widget"`

2. Le lien s'affiche dans la section "Visualisation" de `/catalogue/item/{id}`

```python
@app.route("/api/items/<int:item_id>/viz-links", methods=["POST"])
@login_required
def add_viz_link(item_id):
    data = request.json
    link = VisualizationLink(
        parent_item_id=item_id,
        name=data["name"],
        url=data["url"],
        owner_user_id=current_user.id,
        link_type=data.get("link_type", "external"),
        display_order=request.form.get("display_order", 0)
    )
    db.session.add(link)
    db.session.commit()

    return jsonify({"status": "created", "id": link.id})
```

### 9.3 Affichage dans les templates

**Onglet Données** — `catalogue.html` : afficher tous les items où `is_published=True`, y compris les chunks uploadés par les utilisateurs (filtrage via `type='geodonnee' OR type='user_chunk'`).

**Onglet Visualisation** — `item_detail.html` section "Visualisation" :
```html
<div class="viz-links">
    {% for link in item.visualization_links %}
        <a href="{{ link.url }}" target="_blank">
            {{ link.name }}
        </a>
    {% endfor %}
</div>
```

### 9.4 Worker de traitement (Celery/RQ)

**Fichier :** `workers/processing.py` (nouveau)

```python
from celery import Celery

celery_app = Celery("ananas", broker="redis://redis:6379/0")

@celery_app.task
def process_chunk(upload_id):
    upload = UserUpload.query.get(upload_id)
    chunk = DataChunk.query.get(upload.chunk_id)

    upload.processing_status = "processing"
    db.session.commit()

    # 1. Valider et convertir le fichier
    # 2. Générer métadonnées, taille, format
    # 3. Créer magnet link (si Bittorrent)
    # 4. Mettre à jour DataChunk → is_published=True, publish_at=NOW()
    # 5. Si parent_item_id est NULL → créer un nouvel Item dans le catalogue

    chunk.upload_status = "published"
    chunk.is_published = True
    chunk.published_at = datetime.now()
    db.session.commit()
```
