# Dashboard personnel — Déploiement sur Render

Dashboard Flask affichant météo, tram TAM, actualités IA, todo list et calendrier.

---

## Déploiement sur Render (Web Service)

### 1. Préparer le repo GitHub

```bash
# Supprimer le .env du suivi Git (s'il était déjà commité)
git rm --cached .env
git commit -m "chore: remove .env from tracking"
git push
```

Vérifier que `.gitignore` contient bien `.env` et `data/`.

### 2. Créer le service sur Render

1. [render.com](https://render.com) → **New Web Service**
2. Connecter le repo `gauthierthesis/dashboard`
3. Remplir les champs :

| Champ | Valeur |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 60` |

### 3. Variables d'environnement (Render > Environment)

| Variable | Valeur |
|---|---|
| `SECRET_KEY` | Une chaîne longue et aléatoire |
| `DASHBOARD_PASSWORD` | Ton mot de passe |
| `PYTHON_VERSION` | `3.11.0` |

> ⚠️ **Ne jamais mettre DEBUG=true en production.**

### 4. ⚠️ Filesystem éphémère

Render réinitialise le disque à chaque redéploiement.  
Les fichiers `data/todos.json` et `data/events.json` seront **perdus** à chaque deploy.

**Solutions pérennes :**
- Migrer vers une base de données (SQLite via [Render Disk](https://render.com/docs/disks), ou PostgreSQL gratuit sur Render)
- Utiliser un service externe (Supabase, PlanetScale, etc.)

---

## Développement local

```bash
python -m venv .venv
source .venv/bin/activate       # Windows : .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # puis éditer .env avec tes valeurs
python app.py
```

Ouvrir [http://localhost:5000](http://localhost:5000)

---

## Structure du projet

```
dashboard/
├── app.py              # Application Flask principale
├── config.py           # Configuration centralisée
├── requirements.txt    # Dépendances Python
├── Procfile            # Commande de démarrage pour Render
├── .env.example        # Template de configuration (à copier en .env)
├── .gitignore
├── data/               # Données JSON (ignorées par git, éphémères sur Render)
├── templates/          # Vues Jinja2
│   ├── index.html
│   └── login.html
```
# superdash
