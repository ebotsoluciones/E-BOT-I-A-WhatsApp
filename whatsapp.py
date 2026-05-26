"""
whatsapp.py — WhatsApp Cloud API (Meta)
"""

import requests
import logging
from config import WA_TOKEN, WA_PHONE_ID

logger = logging.getLogger(__name__)

BASE_URL = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages"
HEADERS  = {
    "Authorization": f"Bearer {WA_TOKEN}",
    "Content-Type":  "application/json"
}


def _post(payload: dict) -> bool:
    try:
        r = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            logger.error("Meta API error %s: %s", r.status_code, r.text)
            return False
        return True
    except Exception as e:
        logger.error("Meta API exception: %s", e)
        return False


def enviar_texto(numero: str, texto: str) -> bool:
    return _post({
        "messaging_product": "whatsapp",
        "to":   numero,
        "type": "text",
        "text": {"body": texto, "preview_url": False}
    })


def enviar_imagen_con_botones(numero: str, imagen_url: str, body: str, footer: str, botones: list) -> bool:
    return _post({
        "messaging_product": "whatsapp",
        "to":   numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type":  "image",
                "image": {"link": imagen_url}
            },
            "body":   {"text": body},
            "footer": {"text": footer},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in botones[:3]
                ]
            }
        }
    })


def enviar_interactivo_botones(numero: str, header_text: str, body: str, footer: str, botones: list) -> bool:
    return _post({
        "messaging_product": "whatsapp",
        "to":   numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {"type": "text", "text": header_text},
            "body":   {"text": body},
            "footer": {"text": footer},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in botones[:3]
                ]
            }
        }
    })


def reenviar_a_numero(numero_destino: str, numero_origen: str, mensaje: str) -> bool:
    texto = f"📩 *Nuevo contacto E-Bot*\n\n📱 {numero_origen}\n💬 {mensaje}"
    return enviar_texto(numero_destino, texto)


def marcar_leido(message_id: str):
    _post({
        "messaging_product": "whatsapp",
        "status":     "read",
        "message_id": message_id
    })
