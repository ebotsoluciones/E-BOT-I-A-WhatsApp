import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from flask import Flask, request, jsonify
from config   import WA_VERIFY_TOKEN
from storage  import init_db
from handlers import procesar

app = Flask(__name__)
init_db()


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "bot": "E-Bot Soluciones", "webhook": "/webhook"}), 200


@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == WA_VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


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
        numero  = mensaje["from"]

        if mensaje.get("type") == "text":
            body = mensaje["text"]["body"]
        elif mensaje.get("type") == "interactive":
            # Respuesta de botón interactivo
            interactive = mensaje.get("interactive", {})
            if interactive.get("type") == "button_reply":
                body = interactive["button_reply"]["id"]
            else:
                return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "ok"}), 200
        logging.info("MSG de %s: %s", numero, body)
        procesar(numero, body)
    except (KeyError, IndexError) as e:
        logging.error("Payload error: %s", e)
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=False)
