import os

# ── MODO ──────────────────────────────────────
MODO_TEST = os.getenv("MODO_TEST", "true").lower() == "true"

# ── ADMINS ────────────────────────────────────
# Lista de números en formato internacional sin + (ej: "5493515000000")
ADMINS = os.getenv("ADMINS", "").split(",") if os.getenv("ADMINS") else []

# ── WHATSAPP CLOUD API (Meta) ─────────────────
WA_TOKEN        = os.getenv("WA_TOKEN", "")          # Bearer token permanente
WA_PHONE_ID     = os.getenv("WA_PHONE_ID", "")       # Phone Number ID del dashboard
WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "ebot_verify")  # Token de verificación webhook

# ── SUPABASE / POSTGRESQL ─────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")          # postgresql://user:pass@host:5432/db

# ── OPENAI ────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── BRANDING DEMO ─────────────────────────────
MARCA        = "E-Bot Soluciones"
TELEFONO     = os.getenv("WA_DISPLAY_NUMBER", "+54 351 XXX XXXX")
EMAIL        = "contacto@ebotsoluciones.lat"
WEB          = "https://ebotsoluciones.lat/"
HORARIO      = "Lunes a Viernes de 9:00 a 18:00 hs"
