import os

# ── MODO ──────────────────────────────────────
MODO_TEST = os.getenv("MODO_TEST", "true").lower() == "true"

# ── ADMINS ────────────────────────────────────
ADMINS = os.getenv("ADMINS", "").split(",") if os.getenv("ADMINS") else []

# ── WHATSAPP CLOUD API (Meta) ─────────────────
# Acepta nombre nuevo (WA_TOKEN) o el anterior (META_ACCESS_TOKEN)
WA_TOKEN        = os.getenv("WA_TOKEN") or os.getenv("META_ACCESS_TOKEN", "")
WA_PHONE_ID     = os.getenv("WA_PHONE_ID") or os.getenv("META_PHONE_NUMBER_ID", "")
WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN") or os.getenv("META_VERIFY_TOKEN", "ebot_verify")

# ── SUPABASE / POSTGRESQL ─────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── OPENAI ────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── BRANDING ──────────────────────────────────
MARCA        = "E-Bot Soluciones"
TELEFONO     = os.getenv("WA_DISPLAY_NUMBER", "+54 351 564 5624")
EMAIL        = "contacto@ebotsoluciones.lat"
WEB          = "https://ebotsoluciones.lat/"
HORARIO      = "Lunes a Viernes de 9:00 a 18:00 hs"
