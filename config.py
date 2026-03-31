"""
Configuration centrale du dashboard.
Toutes les valeurs sensibles doivent être définies
dans les variables d'environnement (Render > Environment).

Variables requises en production :
  SECRET_KEY         — clé de session Flask
  DASHBOARD_PASSWORD — mot de passe de connexion
  SUPABASE_URL       — URL du projet Supabase
  SUPABASE_KEY       — clé service_role Supabase (anon key si RLS bien configurée)

Variables optionnelles :
  DEBUG              — "true" pour le mode debug local (jamais en prod)
  PORT               — port d'écoute (défaut: 5000)
  WEATHER_LAT        — latitude météo (défaut: 43.6108, Montpellier)
  WEATHER_LON        — longitude météo (défaut: 3.8767, Montpellier)

  GTFS stop IDs TAM Montpellier (ligne 1) :
  GTFS_STOP_IDS_ALBERT      — stop IDs Albert 1er (défaut: "1195,1222")
                               1195 = sens Mosson→Odysseum
                               1222 = sens Odysseum→Mosson
  GTFS_STOP_IDS_LOUIS_BLANC — stop IDs Louis Blanc (défaut: "1194,1223")
                               1194 = sens Mosson→Odysseum
                               1223 = sens Odysseum→Mosson
  Si le réseau TAM change sa numérotation, ajuster ces valeurs.
  Les IDs réels apparaissent dans les logs en cas d'échec (échantillon stop_ids flux).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Sécurité ────────────────────────────────────────────
SECRET_KEY         = os.getenv("SECRET_KEY", "changez-cette-cle-svp")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

# ── Supabase ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ── Serveur ─────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT  = int(os.getenv("PORT", 5000))

# ── Géolocalisation météo (Montpellier par défaut) ──────
WEATHER_LAT = float(os.getenv("WEATHER_LAT", "43.6108"))
WEATHER_LON = float(os.getenv("WEATHER_LON", "3.8767"))

# ── Stop IDs GTFS-RT TAM (configurables via env vars) ───
GTFS_STOP_IDS_ALBERT      = os.getenv("GTFS_STOP_IDS_ALBERT", "1195,1222")
GTFS_STOP_IDS_LOUIS_BLANC = os.getenv("GTFS_STOP_IDS_LOUIS_BLANC", "1194,1223")
