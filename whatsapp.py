"""
whatsapp.py — Envío de mensajes con WhatsApp Cloud API (Meta)
Soporta: texto simple, mensajes interactivos con botones, imagen + caption
"""

import requests
from config import WA_TOKEN, WA_PHONE_ID

BASE_URL = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages"
HEADERS  = {
    "Authorization": f"Bearer {WA_TOKEN}",
    "Content-Type":  "application/json"
}


def enviar_texto(numero: str, texto: str) -> bool:
    payload = {
        "messaging_product": "whatsapp",
        "to":   numero,
        "type": "text",
        "text": {"body": texto, "preview_url": False}
    }
    r = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=10)
    return r.status_code == 200


def enviar_interactivo_botones(numero: str, header_text: str, body: str, footer: str, botones: list) -> bool:
    """
    Mensaje interactivo con hasta 3 botones.
    botones = [{"id": "btn_1", "title": "Ver DEMO"}, ...]
    """
    payload = {
        "messaging_product": "whatsapp",
        "to":   numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": header_text
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
    }
    r = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=10)
    return r.status_code == 200


def enviar_imagen_con_botones(numero: str, imagen_url: str, body: str, footer: str, botones: list) -> bool:
    """
    Mensaje interactivo con imagen en el header y botones.
    """
    payload = {
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
    }
    r = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=10)
    return r.status_code == 200


def reenviar_a_numero(numero_destino: str, numero_origen: str, mensaje: str) -> bool:
    """Reenvía un mensaje al número del asesor."""
    texto = f"📩 *Nuevo contacto desde E-Bot*\n\n📱 {numero_origen}\n💬 {mensaje}"
    return enviar_texto(numero_destino, texto)


def marcar_leido(message_id: str):
    payload = {
        "messaging_product": "whatsapp",
        "status":     "read",
        "message_id": message_id
    }
    requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=5)
