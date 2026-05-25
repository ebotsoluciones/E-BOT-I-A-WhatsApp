"""
whatsapp.py — Envío de mensajes con WhatsApp Cloud API (Meta)
"""

import requests
from config import WA_TOKEN, WA_PHONE_ID


BASE_URL = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {WA_TOKEN}",
    "Content-Type":  "application/json"
}


def enviar_texto(numero: str, texto: str) -> bool:
    """Envía un mensaje de texto simple."""
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    resp = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=10)
    return resp.status_code == 200


def marcar_leido(message_id: str):
    """Marca un mensaje como leído (doble tilde azul)."""
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=5)
