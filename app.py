"""
app.py — Webhook WhatsApp Cloud API (Meta)

Variables de entorno requeridas:
    WA_TOKEN          Bearer token de Meta
    WA_PHONE_ID       Phone Number ID
    WA_VERIFY_TOKEN   Token de verificación (cualquier string secreto tuyo)
    DATABASE_URL      postgresql://user:pass@host:5432/db
    OPENAI_API_KEY    clave OpenAI
"""

from flask import Flask, request, jsonify
from config   import WA_VERIFY_TOKEN
from handlers import procesar

app = Flask(__name__)


# ── HEALTH CHECK ─────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "bot": "E-Bot Soluciones",
        "webhook": "/webhook"
    }), 200


# ── VERIFICACIÓN DEL WEBHOOK (GET) ────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == WA_VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


# ── RECEPCIÓN DE MENSAJES (POST) ──────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": "no data"}), 200

    try:
        entry   = data["entry"][0]
        changes = entry["changes"][0]["value"]

        # Ignorar si no hay mensajes (ej: status updates de entrega/lectura)
        if "messages" not in changes:
            return jsonify({"status": "ok"}), 200

        mensaje = changes["messages"][0]

        # Solo procesar mensajes de texto
        if mensaje.get("type") != "text":
            return jsonify({"status": "ok"}), 200

        numero = mensaje["from"]          # número en formato internacional
        body   = mensaje["text"]["body"]  # texto del mensaje

        procesar(numero, body)

    except (KeyError, IndexError):
        # Payload inesperado — no crashear
        pass

    # Meta espera siempre 200
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=False)
