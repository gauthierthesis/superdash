# Superdash — Dashboard personnel Montpellier

Dashboard Flask personnel déployé sur Render, affichant en temps réel :

- 🌤 **Météo** — Open-Meteo (gratuit, sans clé API)
- 🚊 **Tramway TAM** — GTFS-RT en temps réel (3 arrêts surveillés)
- 📰 **Actualités IA** — Agrégation parallèle de ~25 flux RSS (cache 15 min)
- ✅ **Todo list** — Persistée côté serveur
- 📅 **Calendrier** — Événements personnels avec mini-agenda hebdomadaire

---

## Déploiement sur Render (Web Service)

### 1. Préparer le repo

```bash
# S'assurer que .env n'est pas tracké
git rm --cached .env 2>/dev/null || true
git commit -m "chore: ensure .env not tracked" --allow-empty
git push
```

Vérifier que `.gitignore` contient bien `.env` et `data/`.

### 2. Créer le service sur Render

1. [render.com](https://render.com) → **New Web Service**
2. Connecter le repo `gauthierthesis/superdash`

| Champ | Valeur |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 60` |

### 3. Variables d'environnement (Render › Environment)

| Variable | Description |
|---|---|
| `SECRET_KEY` | Chaîne aléatoire longue (ex: `openssl rand -hex 32`) |
| `DASHBOARD_PASSWORD` | Mot de passe d'accès au dashboard |
| `PYTHON_VERSION` | `3.11.0` |
| `DEBUG` | `false` en production |

> **Ne jamais mettre `DEBUG=true` en production.**

### 4. ⚠️ Filesystem éphémère

Render réinitialise le disque à chaque redéploiement — les fichiers `data/todos.json` et `data/events.json` sont **perdus** à chaque deploy.

**Solutions pérennes :**
- Render Disk (SQLite persistant)
- PostgreSQL gratuit sur Render
- Service externe : Supabase, PlanetScale, etc.

---

## Développement local

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # puis renseigner .env avec vos valeurs
python app.py
```

Ouvrir <http://localhost:5000>

---

## Arrêts de tram surveillés

Les 3 arrêts de la ligne 1 (et 4) autour de la Place Albert 1er :

| Arrêt | Stop IDs (GTFS-RT) | Lignes |
|---|---|---|
| Albert 1er — Saint-Charles | `1196` (→ Odysseum) · `1221` (→ Mosson) | 1, 4 |
| Albert 1er — Jardin des plantes | `1195` (→ Odysseum) · `1222` (→ Mosson) | 1, 4 |
| Louis Blanc — Agora de la danse | `1194` (→ Odysseum) · `1223` (→ Mosson) | 1, 4 |

> Pour vérifier ou ajuster les stop IDs en production, ouvrir `/api/tram/debug` — il liste tous les `route_id` et `stop_id` du flux GTFS-RT en direct.

**Sources GTFS-RT :**
- `https://proxy.transport.data.gouv.fr/resource/tam-montpellier-gtfs-rt-trip-updates`
- `https://data.montpellier3m.fr/GTFS/Urbain/TripUpdate.pb`

---

## Flux RSS agrégés (actualités IA)

~25 sources dans les catégories : recherche & technique, labs & modèles, actualités tech, réglementation & droit, éthique & société.

Sources principales : Anthropic, OpenAI, Mistral AI, Hugging Face, DeepMind, Google AI, MIT Tech Review, The Verge, TechCrunch, VentureBeat, CNIL, Stanford HAI, AlgorithmWatch…

Le cache serveur est de **15 minutes** — les requêtes client entre deux rafraîchissements servent la version en cache.

---

## Structure du projet

```
superdash/
├── app.py                  # Application Flask principale
├── config.py               # Configuration centralisée (variables d'env)
├── requirements.txt        # Dépendances Python
├── Procfile                # Commande de démarrage pour Render
├── .env.example            # Template de configuration (à copier en .env)
├── .gitignore
├── gtfs_realtime.proto     # Schéma protobuf GTFS-RT
├── gtfs_realtime_pb2.py    # Code généré depuis le .proto
├── data/                   # Données JSON (ignorées par git, éphémères sur Render)
└── templates/
    ├── index.html          # Dashboard principal
    └── login.html          # Page de connexion
```

---

## Sécurité

- Toutes les valeurs sensibles (`SECRET_KEY`, `DASHBOARD_PASSWORD`) sont lues depuis les **variables d'environnement** — aucun secret dans le code source.
- Le fichier `.env` est exclu de git via `.gitignore`.
- L'accès au dashboard est protégé par mot de passe (session Flask signée).
- `DEBUG=false` imposé en production.
