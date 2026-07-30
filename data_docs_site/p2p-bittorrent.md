# P2P & BitTorrent

## Aucune donnée hébergée sur le serveur

**A.N.A.N.A.S. n'héberge aucune donnée sur son serveur.** La plateforme est un catalogue d'indexation : seuls les métadonnées et les **liens magnet** (empreintes cryptographiques) sont stockés dans la base de données. Les données elles-mêmes circulent exclusivement sur le réseau BitTorrent entre les pairs.

Même le cache d'images est géré via qBittorrent en backend — les images de galerie sont également téléchargées depuis le réseau P2P, pas depuis un stockage serveur.

---

## Principe du Peer-to-Peer (P2P)

Le **Peer-to-Peer (P2P)** est un modèle de réseau décentralisé où chaque participant (pair ou *peer*) agit à la fois comme client et serveur. Contrairement au modèle client-serveur classique où un serveur central distribue les données, dans un réseau P2P :

- Chaque pair télécharge des fragments de données depuis d'autres pairs
- Chaque pair **redistribue** simultanément les fragments qu'il possède déjà
- Plus il y a de pairs, plus le réseau est performant et résilient

Ce modèle élimine la dépendance à un serveur central unique, supprimant le **point de défaillance unique** (*Single Point of Failure*).

---

## Le protocole BitTorrent

**BitTorrent** est un protocole de transfert de fichiers P2P conçu pour distribuer de gros volumes de données de manière efficace. Voici son fonctionnement :

1. **Fichier torrent / Magnet link** — Un lien magnet contient un *info hash* (empreinte SHA-1) qui identifie de manière unique le contenu. Aucun fichier torrent n'est nécessaire, le hash suffit.

2. **Tracker** — Serveur qui coordonne les pairs en leur indiquant quels autres pairs possèdent les données recherchées. A.N.A.N.A.S. utilise son propre tracker intégré.

3. **Pairing** — Le client BitTorrent (qBittorrent, Transmission, etc.) contacte le tracker, obtient la liste des pairs, et établit des connexions directes.

4. **Échange de fragments** — Les fichiers sont divisés en *morceaux* (pieces). Les pairs s'échangent ces morceaux selon une stratégie *rarest-first* (les morceaux les plus rares sont prioritaires).

5. **Intégrité** — Chaque morceau est vérifié par hachage SHA-1. Les morceaux corrompus sont rejetés et retéléchargés.

6. **Seeders / Leechers** — Un *seeder* possède l'intégralité des données et les partage. Un *leecher* est en cours de téléchargement. Le système fonctionne tant qu'au moins un seeder est actif.

---

## Avantages du P2P pour la distribution géospatiale

| Avantage | Description |
|----------|-------------|
| **Décentralisation** | Pas de dépendance à un serveur central ou à un hébergeur |
| **Résilience** | Les données restent accessibles même si le portail principal est hors ligne |
| **Passage à l'échelle** | Plus de demandes = plus de pairs = meilleure bande passante agrégée |
| **Intégrité** | Vérification SHA-1 de chaque fragment téléchargé |
| **Coût** | Bande passante mutualisée entre tous les participants |
| **Redondance** | Multiples copies des données sur le réseau |

---

## Client torrent recommandé

A.N.A.N.A.S. utilise **qBittorrent** en backend pour le cache d'images (téléchargement P2P des visuels de galerie). Pour télécharger les données depuis les magnet links, nous recommandons :

- **qBittorrent** — Libre, open-source, multi-plateforme
- **Transmission** — Léger, idéal pour les serveurs
- **Deluge** — Extensible via plugins