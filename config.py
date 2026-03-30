"""
Configuration centrale du dashboard.
Toutes les valeurs sensibles doivent être définies
dans les variables d'environnement (Render > Environment).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Sécurité ────────────────────────────────────────────
SECRET_KEY         = os.getenv("SECRET_KEY", "changez-cette-cle-svp")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

# ── Serveur ─────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT  = int(os.getenv("PORT", 5000))

# ── Chemins ─────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
TODOS_FILE  = os.path.join(DATA_DIR, "todos.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")

# ── Géolocalisation météo (Montpellier par défaut) ──────
WEATHER_LAT = float(os.getenv("WEATHER_LAT", "43.6108"))
WEATHER_LON = float(os.getenv("WEATHER_LON", "3.8767"))

# ── Arrêt de tram surveillé ─────────────────────────────
TRAM_STOP_FILTER = os.getenv("TRAM_STOP_FILTER", "ALBERT")
