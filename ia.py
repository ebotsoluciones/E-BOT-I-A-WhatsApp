import json
import os
from openai import OpenAI

PROMPT_BASE = """Interpretá el mensaje y respondé SOLO con JSON, sin texto extra, sin backticks.

Intenciones posibles: crear_turno, ver_turnos, cancelar_turno, consulta_general, desconocido

Ejemplos:
"quiero un turno" -> {"intent":"crear_turno","fecha":"","hora":"","mensaje":""}
"mis turnos" -> {"intent":"ver_turnos","fecha":"","hora":"","mensaje":""}
"cancelar turno" -> {"intent":"cancelar_turno","fecha":"","hora":"","mensaje":""}
"urgencia" -> {"intent":"consulta_general","fecha":"","hora":"","mensaje":"Te comunico con urgencias"}
"mensaje" -> {"intent":"consulta_general","fecha":"","hora":"","mensaje":"Dejame tu mensaje"}
"hola" -> {"intent":"consulta_general","fecha":"","hora":"","mensaje":"¡Hola! ¿En qué puedo ayudarte?"}

Extraer fecha (dd/mm/yyyy) y hora (HH:MM) si están presentes.
Responder SOLO JSON."""


def interpretar_mensaje(texto_usuario: str) -> dict:
    try:
        client = OpenAI(
            api_key=os.getenv("NVIDIA_API_KEY"),
            base_url="https://integrate.api.nvidia.com/v1",
            timeout=8.0  # máximo 8 segundos
        )

        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": PROMPT_BASE},
                {"role": "user",   "content": texto_usuario}
            ],
            temperature=0.1,
            max_tokens=100
        )

        contenido = response.choices[0].message.content.strip()

        # Limpiar backticks si los hay
        if "```" in contenido:
            partes = contenido.split("```")
            contenido = partes[1] if len(partes) > 1 else partes[0]
            if contenido.startswith("json"):
                contenido = contenido[4:]

        # Extraer solo el JSON si hay texto extra
        inicio = contenido.find("{")
        fin    = contenido.rfind("}") + 1
        if inicio >= 0 and fin > inicio:
            contenido = contenido[inicio:fin]

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
