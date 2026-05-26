from flask import Flask, request, jsonify
from config   import WA_VERIFY_TOKEN
from storage  import init_db
from handlers import procesar

app = Flask(__name__)

# Crea las tablas en PostgreSQL si no existen
init_db()


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────
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

        if "messages" not in changes:
            return jsonify({"status": "ok"}), 200

        mensaje = changes["messages"][0]

        if mensaje.get("type") != "text":
            return jsonify({"status": "ok"}), 200

        numero = mensaje["from"]
        body   = mensaje["text"]["body"]

        procesar(numero, body)

    except (KeyError, IndexError):
        pass

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=False)
