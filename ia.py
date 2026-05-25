import json
import os
from openai import OpenAI

PROMPT_BASE = """
Sos un asistente de WhatsApp para gestión de turnos de un negocio.

Tu función NO es conversar libremente ni tomar decisiones finales.
Tu función es interpretar mensajes de usuarios y devolver información estructurada.

Intenciones posibles:
- crear_turno
- ver_turnos
- cancelar_turno
- consulta_general
- desconocido

Extraer si están presentes:
- fecha (formato dd/mm/yyyy si es posible)
- hora  (formato HH:MM si es posible)

Responder SIEMPRE en JSON puro, sin backticks, sin texto extra:

{
  "intent": "",
  "fecha": "",
  "hora": "",
  "mensaje": ""
}
"""


def interpretar_mensaje(texto_usuario: str) -> dict:
    try:
        # Cliente lazy — se crea solo cuando se llama, no al importar
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_BASE},
                {"role": "user",   "content": texto_usuario}
            ],
            temperature=0.2,
            max_tokens=200
        )

        contenido = response.choices[0].message.content.strip()

        if "```" in contenido:
            contenido = contenido.split("```")[1]
            if contenido.startswith("json"):
                contenido = contenido[4:]

        data = json.loads(contenido)

        return {
            "intent":  data.get("intent",  "desconocido"),
            "fecha":   data.get("fecha",   ""),
            "hora":    data.get("hora",    ""),
            "mensaje": data.get("mensaje", "")
        }

    except Exception:
        return {
            "intent":  "desconocido",
            "fecha":   "",
            "hora":    "",
            "mensaje": ""
        }
