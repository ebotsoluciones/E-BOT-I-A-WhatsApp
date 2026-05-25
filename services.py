from datetime import time

# ── CONFIG HORARIOS ───────────────────────────
HORA_INICIO = time(9, 0)
HORA_FIN    = time(19, 0)
INTERVALO   = 60  # minutos


def generar_horarios() -> list:
    horarios = []
    h, m = HORA_INICIO.hour, HORA_INICIO.minute
    while (h, m) <= (HORA_FIN.hour, HORA_FIN.minute):
        horarios.append(f"{h:02d}:{m:02d}")
        m += INTERVALO
        h += m // 60
        m  %= 60
    return horarios


def normalizar_hora(texto: str):
    texto = texto.strip().replace(".", ":").replace("-", ":")
    if ":" not in texto:
        texto += ":00"
    try:
        h, m = map(int, texto.split(":"))
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    except Exception:
        pass
    return None
