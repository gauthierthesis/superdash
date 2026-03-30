from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from dotenv import load_dotenv
from functools import wraps
import json, os, csv, io, re, feedparser, requests
from datetime import datetime, timedelta
import logging
import gtfs_realtime_pb2  # généré localement depuis gtfs_realtime.proto

load_dotenv()

# ══════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changez-cette-cle-svp")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

# Logging structuré pour Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de données
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
TODOS_FILE  = os.path.join(DATA_DIR, "todos.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")

# Création automatique du dossier data au démarrage
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════
# HELPERS GÉNÉRIQUES
# ══════════════════════════════════════
def load_json(path: str, default=None):
    """Charge un fichier JSON, retourne default si absent ou invalide."""
    if default is None:
        default = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(path: str, data):
    """Sauvegarde data en JSON (crée le dossier si nécessaire)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════
# AUTHENTIFICATION
# ══════════════════════════════════════
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not DASHBOARD_PASSWORD or session.get("logged_in"):
            return f(*args, **kwargs)
        return redirect(url_for("login"))
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Mot de passe incorrect"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ══════════════════════════════════════
# PAGE PRINCIPALE
# ══════════════════════════════════════
@app.route("/")
@login_required
def index():
    return render_template("index.html")

# ══════════════════════════════════════
# TODO LIST
# ══════════════════════════════════════
@app.route("/api/todos", methods=["GET"])
@login_required
def get_todos():
    return jsonify(load_json(TODOS_FILE))

@app.route("/api/todos", methods=["POST"])
@login_required
def save_todos():
    todos = request.get_json()
    if not isinstance(todos, list):
        return jsonify({"error": "Format invalide"}), 400
    save_json(TODOS_FILE, todos)
    return jsonify({"status": "ok"})

# ══════════════════════════════════════
# CALENDRIER LOCAL
# ══════════════════════════════════════
@app.route("/api/events", methods=["GET"])
@login_required
def get_events():
    try:
        events  = load_json(EVENTS_FILE)
        now     = datetime.now()
        upcoming = []
        for e in events:
            try:
                dt = datetime.fromisoformat(e["date"])
                if dt < now:
                    continue
                date_str = (
                    dt.strftime("%d %b")
                    if (dt.hour == 0 and dt.minute == 0)
                    else dt.strftime("%d %b à %H:%M")
                )
                upcoming.append({
                    "id":    e.get("id", ""),
                    "title": e["title"],
                    "date":  date_str,
                    "raw":   e["date"],
                })
            except (KeyError, ValueError):
                continue
        upcoming.sort(key=lambda x: x["raw"])
        return jsonify(upcoming[:8])
    except Exception as e:
        logger.error("Erreur events : %s", e)
        return jsonify([])

@app.route("/api/events", methods=["POST"])
@login_required
def add_event():
    try:
        data  = request.get_json()
        title = data.get("title", "").strip()
        date  = data.get("date", "").strip()
        if not title or not date:
            return jsonify({"error": "title et date sont requis"}), 400
        datetime.fromisoformat(date)  # valide le format
        events = load_json(EVENTS_FILE)
        events.append({
            "id":    str(datetime.now().timestamp()),
            "title": title,
            "date":  date,
        })
        save_json(EVENTS_FILE, events)
        return jsonify({"status": "ok"})
    except ValueError:
        return jsonify({"error": "Format de date invalide (ISO 8601 attendu)"}), 400
    except Exception as e:
        logger.error("Erreur add_event : %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/events/<event_id>", methods=["DELETE"])
@login_required
def delete_event(event_id):
    try:
        events = [e for e in load_json(EVENTS_FILE) if e.get("id") != event_id]
        save_json(EVENTS_FILE, events)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error("Erreur delete_event : %s", e)
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════
# MÉTÉO — Open-Meteo (gratuit, sans clé)
# ══════════════════════════════════════
@app.route("/api/weather")
@login_required
def get_weather():
    try:
        res = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":      43.6108,
                "longitude":     3.8767,
                "current":       "temperature_2m,weathercode,windspeed_10m,relativehumidity_2m,apparent_temperature",
                "daily":         "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone":      "Europe/Paris",
                "forecast_days": 5,
            },
            timeout=10,
        )
        res.raise_for_status()
        data    = res.json()
        current = data.get("current", {})
        daily   = data.get("daily", {})
        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        forecast = []
        for i in range(min(5, len(daily.get("time", [])))):
            dt = datetime.fromisoformat(daily["time"][i])
            forecast.append({
                "day":  "Auj." if i == 0 else days_fr[dt.weekday()],
                "code": daily["weathercode"][i],
                "max":  round(daily["temperature_2m_max"][i]),
                "min":  round(daily["temperature_2m_min"][i]),
                "rain": round(daily.get("precipitation_sum", [0] * 5)[i], 1),
            })
        return jsonify({
            "temp":       round(current.get("temperature_2m", 0)),
            "feels_like": round(current.get("apparent_temperature", 0)),
            "code":       current.get("weathercode", 0),
            "wind":       round(current.get("windspeed_10m", 0)),
            "humidity":   round(current.get("relativehumidity_2m", 0)),
            "forecast":   forecast,
        })
    except requests.RequestException as e:
        logger.error("Erreur météo (réseau) : %s", e)
        return jsonify({"error": "Service météo indisponible"}), 503
    except Exception as e:
        logger.error("Erreur météo : %s", e)
        return jsonify({}), 500

# ══════════════════════════════════════
# TRAM — GTFS-RT TAM Montpellier
# Flux protobuf officiel, sans clé API
# 2 arrêts surveillés : Albert 1er + Louis Blanc
# ══════════════════════════════════════
TAM_COLORS = {
    "1": "#009FE3",
    "2": "#E2001A",
    "3": "#00A550",
    "4": "#8B5CA5",
    "5": "#F39200",
    "6": "#E5007D",
    "7": "#B2C800",
    "8": "#009FE3",
    "9": "#6DBEAA",
}

# Flux GTFS-RT TripUpdates — essayé dans l'ordre
GTFS_RT_URLS = [
    "https://proxy.transport.data.gouv.fr/resource/tam-montpellier-gtfs-rt-trip-updates",
    "https://data.montpellier3m.fr/GTFS/Urbain/TripUpdate.pb",
]

# Configuration des arrêts surveillés.
# stop_ids : entiers courts utilisés dans le flux GTFS-RT TAM.
# patterns : correspondance partielle sur stop_id textuel (fallback si IDs changent).
# Les vrais IDs seront confirmés dans les logs après le premier déploiement.
# Stop IDs identifiés depuis les séquences réelles du flux GTFS-RT TAM
# Ligne 1, sens Mosson→Odysseum : Albert=1195, Louis Blanc=1194
# Ligne 1, sens Odysseum→Mosson : Albert=1222, Louis Blanc=1223
WATCHED_STOPS = [
    {
        "label":    "Albert 1er — Jardin des plantes",
        "stop_ids": {"1195", "1222"},
        "patterns": [],
    },
    {
        "label":    "Louis Blanc — Agora de la danse",
        "stop_ids": {"1194", "1223"},
        "patterns": [],
    },
]

def _fetch_gtfs_rt() -> bytes:
    """Télécharge le flux GTFS-RT en essayant plusieurs URLs."""
    headers = {"User-Agent": "Mozilla/5.0 (dashboard/1.0)"}
    for url in GTFS_RT_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            if len(r.content) > 100:
                logger.info("GTFS-RT récupéré depuis %s (%d bytes)", url, len(r.content))
                return r.content
        except Exception as e:
            logger.warning("GTFS-RT indisponible (%s) : %s", url, e)
    raise RuntimeError("Aucune source GTFS-RT disponible")

def _stop_matches(sid: str, stop_cfg: dict) -> bool:
    """Vérifie si un stop_id correspond à un arrêt surveillé (ID exact ou pattern)."""
    if sid in stop_cfg["stop_ids"]:
        return True
    sid_upper = sid.upper()
    return any(p in sid_upper for p in stop_cfg["patterns"])

def _parse_passages(feed, now) -> list:
    """Extrait tous les passages à venir pour les arrêts surveillés."""
    passages = []
    all_ids_seen = set()  # pour diagnostic

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        tu       = entity.trip_update
        route_id = tu.trip.route_id
        headsign = getattr(tu.trip, "trip_headsign", "")

        for stu in tu.stop_time_update:
            sid = str(stu.stop_id)
            all_ids_seen.add(sid)

            # Cherche quel arrêt surveillé correspond
            matched_stop = None
            for stop_cfg in WATCHED_STOPS:
                if _stop_matches(sid, stop_cfg):
                    matched_stop = stop_cfg
                    break
            if not matched_stop:
                continue

            # Heure de départ (ou arrivée si absent)
            if stu.HasField("departure"):
                ts, delay = stu.departure.time, stu.departure.delay
            elif stu.HasField("arrival"):
                ts, delay = stu.arrival.time, stu.arrival.delay
            else:
                continue

            depart = datetime.fromtimestamp(ts)
            if depart < now:
                continue
            diff = int((depart - now).total_seconds() / 60)
            if diff > 60:
                continue

            line = route_id.lstrip("0") if route_id else "?"
            dest = headsign.title() if headsign else "—"

            passages.append({
                "stop":      matched_stop["label"],
                "line":      line,
                "color":     TAM_COLORS.get(line, "#6B6560"),
                "direction": dest,
                "minutes":   diff,
                "time":      depart.strftime("%H:%M"),
                "realtime":  delay != 0,
            })

    return passages, all_ids_seen

@app.route("/api/tram")
@login_required
def get_tram():
    try:
        raw  = _fetch_gtfs_rt()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(raw)
        now  = datetime.now()

        passages, all_ids = _parse_passages(feed, now)

        # Dédoublonner par (arrêt, ligne, direction, minute)
        seen, unique = set(), []
        for p in sorted(passages, key=lambda x: (x["stop"], x["minutes"])):
            key = (p["stop"], p["line"], p["direction"], p["minutes"])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        if not unique:
            logger.warning(
                "0 passage trouvé. Échantillon stop_ids flux : %s",
                sorted(all_ids)[:80]
            )
            return jsonify({"error": "Aucun passage — stop_ids à ajuster"}), 404

        return jsonify(unique[:12])

    except RuntimeError as e:
        logger.error("Tram source : %s", e)
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error("Erreur tram : %s", e)
        return jsonify({"error": "Erreur interne"}), 500

# ══════════════════════════════════════
# ACTUALITÉS IA — Flux RSS natifs
# ══════════════════════════════════════
# Catégories : recherche, produits, réglementation/droit, éthique, business
AI_FEEDS = {
    # ── Recherche & technique ────────────────────────────────────
    "MIT Tech Review": {
        "url":  "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",
        "icon": "🔬",
    },
    "Hugging Face": {
        "url":  "https://huggingface.co/blog/feed.xml",
        "icon": "🤗",
    },
    "DeepMind": {
        "url":  "https://deepmind.google/blog/rss.xml",
        "icon": "🧬",
    },
    "Google AI": {
        "url":  "https://blog.research.google/feeds/posts/default?alt=rss",
        "icon": "🔵",
    },
    "Meta AI": {
        "url":  "https://ai.meta.com/blog/rss/",
        "icon": "🟦",
    },
    "Papers With Code": {
        "url":  "https://paperswithcode.com/latest.rss",
        "icon": "📄",
    },
    # ── Labs & modèles ───────────────────────────────────────────
    "Anthropic": {
        "url":  "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_claude.xml",
        "icon": "🧠",
    },
    "OpenAI": {
        "url":  "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_openai_research.xml",
        "icon": "✦",
    },
    "Mistral AI": {
        "url":  "https://mistral.ai/news/rss.xml",
        "icon": "💨",
    },
    "Cohere": {
        "url":  "https://cohere.com/blog/rss",
        "icon": "🔷",
    },
    # ── Actualités tech & IA ─────────────────────────────────────
    "The Verge AI": {
        "url":  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "icon": "⚡",
    },
    "VentureBeat IA": {
        "url":  "https://venturebeat.com/category/ai/feed/",
        "icon": "📡",
    },
    "Wired AI": {
        "url":  "https://www.wired.com/feed/tag/artificial-intelligence/latest/rss",
        "icon": "🌐",
    },
    "TechCrunch AI": {
        "url":  "https://techcrunch.com/category/artificial-intelligence/feed/",
        "icon": "🚀",
    },
    "Ars Technica AI": {
        "url":  "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "icon": "🖥",
    },
    "Import AI": {
        "url":  "https://importai.substack.com/feed",
        "icon": "📨",
    },
    "The Batch (DeepLearning.AI)": {
        "url":  "https://read.deeplearning.ai/the-batch/rss/",
        "icon": "📦",
    },
    # ── Réglementation, droit & politique ────────────────────────
    "AI Policy (Future of Life)": {
        "url":  "https://futureoflife.org/feed/",
        "icon": "⚖️",
    },
    "European Parliament AI": {
        "url":  "https://www.europarl.europa.eu/rss/doc/news-articles/en.rss",
        "icon": "🇪🇺",
    },
    "CNIL": {
        "url":  "https://www.cnil.fr/fr/rss.xml",
        "icon": "🛡",
    },
    "AI Now Institute": {
        "url":  "https://ainowinstitute.org/feed",
        "icon": "📜",
    },
    "Stanford HAI": {
        "url":  "https://hai.stanford.edu/news/rss.xml",
        "icon": "🏛",
    },
    "Brookings AI": {
        "url":  "https://www.brookings.edu/topic/artificial-intelligence/feed/",
        "icon": "🏦",
    },
    # ── Éthique & société ────────────────────────────────────────
    "AlgorithmWatch": {
        "url":  "https://algorithmwatch.org/en/feed/",
        "icon": "🔍",
    },
    "Partnership on AI": {
        "url":  "https://partnershiponai.org/feed/",
        "icon": "🤝",
    },
    "Mozilla Foundation AI": {
        "url":  "https://foundation.mozilla.org/en/feed/blog/",
        "icon": "🦊",
    },
}

RSS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

@app.route("/api/news")
@login_required
def get_news():
    articles = []
    now      = datetime.now()

    for source, meta in AI_FEEDS.items():
        try:
            res  = requests.get(meta["url"], headers=RSS_HEADERS, timeout=8)
            feed = feedparser.parse(res.text)
            for entry in feed.entries[:2]:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    dt   = datetime(*published[:6])
                    diff = now - dt
                    if diff.days > 7:
                        continue
                    if diff.days > 0:
                        time_str = f"il y a {diff.days}j"
                    elif diff.seconds > 3600:
                        time_str = f"il y a {diff.seconds // 3600}h"
                    else:
                        time_str = f"il y a {diff.seconds // 60}min"
                else:
                    time_str = ""
                    dt = now

                title   = entry.get("title", "Sans titre")
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:160]

                articles.append({
                    "source":  source,
                    "icon":    meta["icon"],
                    "title":   title,
                    "summary": summary,
                    "time":    time_str,
                    "link":    entry.get("link", ""),
                    "_dt":     dt.isoformat(),
                })
        except Exception as e:
            logger.warning("Erreur flux %s : %s", source, e)
            continue

    articles.sort(key=lambda x: x.pop("_dt", ""), reverse=True)
    return jsonify(articles[:12])

# Alias rétrocompatibilité
@app.route("/api/twitter")
@login_required
def get_twitter():
    return get_news()

# ══════════════════════════════════════
# POINT D'ENTRÉE (dev local uniquement)
# ══════════════════════════════════════
if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=debug_mode
    )
