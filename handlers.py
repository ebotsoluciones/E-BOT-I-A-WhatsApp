from datetime import datetime

from storage import (
    get_full_state, set_user_state, clear_user,
    turnos_usuario, agregar_turno, cancelar_turno,
    horarios_libres, guardar_mensaje,
    bloquear_horario, turnos_por_fecha, obtener_mensajes
)
from services  import normalizar_hora
from ia        import interpretar_mensaje
from whatsapp  import enviar_texto
from config    import ADMINS, MODO_TEST, MARCA, TELEFONO, EMAIL, WEB, HORARIO


# ═══════════════════════════════════════════════════════════
# MENSAJES DEL FUNNEL
# ═══════════════════════════════════════════════════════════

MSG_PRESENTACION = """🤖 *¡Hola! Soy E-Bot*
_Automatización inteligente de turnos por WhatsApp_

📍 Córdoba, Argentina
🌐 ebotsoluciones.lat

Ayudo a negocios como el tuyo a:
✅ Gestionar turnos automáticamente
✅ Atender clientes 24/7
✅ Eliminar llamadas y confusiones

¿Qué querés hacer?

1️⃣ Ver una *DEMO* personalizada
2️⃣ Hablar con un *asesor*"""

MSG_PEDIR_NOMBRE = """🎯 *¡Genial! Vamos a personalizar tu demo.*

¿Cómo se llama tu negocio?
_(Ej: Consultorio Dra. López, Estudio Barlovento, Clínica San Marcos)_"""

MSG_CONTACTO = """💬 *¡Con gusto te asesoramos!*

Dejanos tu consulta o nombre y te contactamos a la brevedad.

📞 {tel}
✉️ {email}
🌐 {web}

_O simplemente escribí tu mensaje ahora:_"""

MSG_CIERRE_DEMO = """🚀 *¿Te convenciste?*

Implementamos E-Bot en tu negocio en 48hs.

¿Qué querés hacer?

1️⃣ Quiero que me contacten
2️⃣ Tengo una pregunta
3️⃣ Volver al menú demo"""

MSG_LEAD = """✅ *¡Perfecto! Registramos tu interés.*

Un asesor de E-Bot Soluciones te va a contactar pronto.

📞 {tel}
✉️ {email}
🌐 {web}

_¡Gracias por tu tiempo!_"""

MSG_DESPEDIDA = """✅ *Gracias por probar E-Bot{nombre}*

Horario de atención: {horario}

📞 {tel}
✉️ {email}
🌐 {web}

💬 Escribí *hola* para volver a empezar."""


def _menu_demo(nombre):
    return (
        f"🎉 *¡Bienvenido/a, {nombre}!*\n\n"
        f"Esto es lo que E-Bot puede hacer por tu negocio 👇\n\n"
        f"1️⃣  Sacar un turno\n"
        f"2️⃣  Ver mis turnos\n"
        f"3️⃣  Dejar un mensaje\n"
        f"4️⃣  Urgencia\n"
        f"0️⃣  Salir\n\n"
        f"_Escribí el número o contame qué necesitás._"
    )

def _menu_simple(nombre):
    return (
        f"🦙 *E-Bot*\n\n"
        f"Hola, *{nombre}* 👋\n\n"
        f"1️⃣  Sacar un turno\n"
        f"2️⃣  Ver mis turnos\n"
        f"3️⃣  Dejar un mensaje\n"
        f"4️⃣  Urgencia\n"
        f"0️⃣  Salir"
    )


# ═══════════════════════════════════════════════════════════
# PROCESADOR PRINCIPAL
# ═══════════════════════════════════════════════════════════

def procesar(numero: str, body: str):
    texto   = body.strip()
    texto_l = texto.lower()

    full   = get_full_state(numero)
    estado = full["estado"]
    datos  = full["datos"]
    nombre = datos.get("nombre_negocio", "")

    # ── ADMIN ────────────────────────────────────────────────
    numero_limpio = numero.replace("whatsapp:", "").replace("+", "")
    if numero_limpio in ADMINS or (MODO_TEST and texto_l == "adm"):
        if estado != "ADMIN_MENU" and texto_l == "adm":
            set_user_state(numero, "estado", "ADMIN_MENU")
            enviar_texto(numero, MENU_ADMIN)
            return
        if estado == "ADMIN_MENU":
            _manejar_admin(numero, texto)
            return
        if estado in ("ADMIN_BLOQUEO_FECHA", "ADMIN_BLOQUEO_HORA"):
            _admin_bloqueo(numero, texto, estado)
            return

    # ── RESET ────────────────────────────────────────────────
    if texto_l in ["hola", "menu", "/start", "inicio", "reiniciar"]:
        clear_user(numero)
        enviar_texto(numero, MSG_PRESENTACION)
        set_user_state(numero, "estado", "FUNNEL_INICIO")
        return

    # ── FUNNEL: PRIMER CONTACTO ───────────────────────────────
    if estado == "MENU" and not nombre:
        enviar_texto(numero, MSG_PRESENTACION)
        set_user_state(numero, "estado", "FUNNEL_INICIO")
        return

    # ── FUNNEL: ELECCIÓN INICIAL ──────────────────────────────
    if estado == "FUNNEL_INICIO":
        if texto in ["1", "demo", "ver demo"]:
            set_user_state(numero, "estado", "FUNNEL_PEDIR_NOMBRE")
            enviar_texto(numero, MSG_PEDIR_NOMBRE)
        elif texto in ["2", "asesor", "hablar", "contacto"]:
            set_user_state(numero, "estado", "FUNNEL_CONTACTO_MSG")
            enviar_texto(numero, MSG_CONTACTO.format(tel=TELEFONO, email=EMAIL, web=WEB))
        else:
            enviar_texto(numero, MSG_PRESENTACION)
        return

    # ── FUNNEL: CAPTURA NOMBRE ────────────────────────────────
    if estado == "FUNNEL_PEDIR_NOMBRE":
        if len(texto.strip()) < 2:
            enviar_texto(numero, "Por favor ingresá un nombre válido.")
            return
        set_user_state(numero, "nombre_negocio", texto.strip())
        set_user_state(numero, "estado", "MENU")
        enviar_texto(numero, _menu_demo(texto.strip()))
        return

    # ── FUNNEL: MENSAJE DE CONTACTO ───────────────────────────
    if estado == "FUNNEL_CONTACTO_MSG":
        guardar_mensaje("Lead", numero, texto)
        enviar_texto(numero, MSG_LEAD.format(tel=TELEFONO, email=EMAIL, web=WEB))
        set_user_state(numero, "estado", "MENU")
        return

    # ── CIERRE DE DEMO ────────────────────────────────────────
    if estado == "FUNNEL_CIERRE":
        if texto == "1":
            set_user_state(numero, "estado", "FUNNEL_CONTACTO_MSG")
            enviar_texto(numero, "✍️ Dejanos tu nombre y consulta, te contactamos:")
        elif texto == "2":
            set_user_state(numero, "estado", "FUNNEL_CONTACTO_MSG")
            enviar_texto(numero, "✍️ Escribí tu pregunta:")
        elif texto == "3":
            set_user_state(numero, "estado", "MENU")
            enviar_texto(numero, _menu_simple(nombre))
        else:
            enviar_texto(numero, MSG_CIERRE_DEMO)
        return

    # ── SALIR ─────────────────────────────────────────────────
    if texto_l in ["0", "salir", "chau", "bye"]:
        nombre_fmt = f", *{nombre}*" if nombre else ""
        enviar_texto(numero, MSG_DESPEDIDA.format(
            nombre=nombre_fmt, horario=HORARIO,
            tel=TELEFONO, email=EMAIL, web=WEB
        ))
        # Mostrar opción de contacto comercial
        enviar_texto(numero, MSG_CIERRE_DEMO)
        set_user_state(numero, "estado", "FUNNEL_CIERRE")
        return

    # ── ESTADOS DE FLUJO ──────────────────────────────────────
    if estado == "MENSAJE":
        guardar_mensaje("Paciente", numero, texto)
        enviar_texto(numero, "✅ Mensaje recibido. Te responderemos a la brevedad.")
        set_user_state(numero, "estado", "MENU")
        return

    if estado == "TURNO_NOMBRE":
        set_user_state(numero, "turno_nombre", texto)
        set_user_state(numero, "estado", "TURNO_FECHA")
        enviar_texto(numero, "📅 Ingresá la fecha del turno (dd/mm/yyyy):")
        return

    if estado == "TURNO_FECHA":
        _flujo_turno_fecha(numero, texto)
        return

    if estado == "TURNO_HORA":
        _flujo_turno_hora(numero, texto, nombre)
        return

    if estado == "CANCEL_FECHA":
        _flujo_cancel_fecha(numero, texto)
        return

    if estado == "CANCEL_HORA":
        _flujo_cancel_hora(numero, texto, nombre)
        return

    # ── MENU PRINCIPAL (con IA) ───────────────────────────────
    if estado == "MENU":
        _procesar_menu(numero, texto, body, nombre)
        return

    # Fallback
    enviar_texto(numero, _menu_simple(nombre) if nombre else MSG_PRESENTACION)


# ═══════════════════════════════════════════════════════════
# MENÚ CON IA + NUMÉRICO
# ═══════════════════════════════════════════════════════════

def _procesar_menu(numero, texto, body_original, nombre):
    # Numérico primero (instantáneo)
    if texto.strip() in ["1", "2", "3", "4"]:
        _menu_numerico(numero, texto.strip(), nombre)
        return

    # IA para lenguaje natural
    resultado = interpretar_mensaje(body_original)
    intent    = resultado["intent"]
    mensaje   = resultado["mensaje"]

    if intent == "crear_turno":
        _iniciar_turno(numero)
    elif intent == "ver_turnos":
        _mis_turnos(numero, nombre)
    elif intent == "cancelar_turno":
        set_user_state(numero, "estado", "CANCEL_FECHA")
        enviar_texto(numero, "Indicá la fecha del turno a cancelar (dd/mm/yyyy):")
    elif intent == "consulta_general" and mensaje:
        enviar_texto(numero, f"🤖 {mensaje}")
        enviar_texto(numero, _menu_simple(nombre))
    else:
        enviar_texto(numero, _menu_simple(nombre))


def _menu_numerico(numero, opcion, nombre):
    if opcion == "1":
        _iniciar_turno(numero)
    elif opcion == "2":
        _mis_turnos(numero, nombre)
    elif opcion == "3":
        set_user_state(numero, "estado", "MENSAJE")
        enviar_texto(numero, "✍️ Escribí tu mensaje y lo registramos:")
    elif opcion == "4":
        enviar_texto(numero, f"🚨 *Urgencias*\n\n📞 {TELEFONO}\n✉️ {EMAIL}")


# ═══════════════════════════════════════════════════════════
# ACCIONES
# ═══════════════════════════════════════════════════════════

def _iniciar_turno(numero):
    set_user_state(numero, "estado", "TURNO_NOMBRE")
    enviar_texto(numero, "👤 ¿Nombre y apellido del paciente?")


def _mis_turnos(numero, nombre):
    lista = turnos_usuario(numero)
    if not lista:
        enviar_texto(numero, "📋 No tenés turnos próximos registrados.")
    else:
        lineas = "\n".join(f"📅 {t['fecha']} {t['hora']} — {t['nombre']}" for t in lista)
        enviar_texto(numero, f"*Tus turnos:*\n\n{lineas}")


# ═══════════════════════════════════════════════════════════
# FLUJO TURNO
# ═══════════════════════════════════════════════════════════

def _flujo_turno_fecha(numero, texto):
    try:
        fecha = datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        enviar_texto(numero, "❌ Formato inválido. Usá dd/mm/yyyy (ej: 27/05/2025)")
        return

    if fecha < datetime.now().date():
        enviar_texto(numero, "❌ La fecha ya pasó. Ingresá una fecha futura:")
        return

    fecha_str = fecha.strftime("%d/%m/%Y")
    set_user_state(numero, "turno_fecha", fecha_str)

    libres = horarios_libres(fecha_str)
    if not libres:
        enviar_texto(numero, f"😔 Sin disponibilidad para el {fecha_str}. Probá otra fecha:")
        return

    set_user_state(numero, "estado", "TURNO_HORA")
    horarios_txt = "\n".join(f"🕐 {h}" for h in libres)
    enviar_texto(numero, f"*Horarios disponibles — {fecha_str}:*\n\n{horarios_txt}\n\n_Respondé con el horario (ej: 10:00 o simplemente 10)_")


def _flujo_turno_hora(numero, texto, nombre):
    hora = normalizar_hora(texto)
    if not hora:
        enviar_texto(numero, "❌ Hora inválida. Usá formato HH:MM (ej: 10:00 o 14)")
        return

    full   = get_full_state(numero)
    datos  = full["datos"]
    fecha  = datos.get("turno_fecha", "")
    nombre_paciente = datos.get("turno_nombre", "")

    libres = horarios_libres(fecha)
    if hora not in libres:
        enviar_texto(numero, f"⚠️ El horario {hora} ya no está disponible. Elegí otro:")
        enviar_texto(numero, "\n".join(f"🕐 {h}" for h in libres))
        return

    agregar_turno(nombre_paciente, numero, fecha, hora)
    enviar_texto(numero, (
        f"✅ *¡Turno confirmado!*\n\n"
        f"👤 {nombre_paciente}\n"
        f"📅 {fecha} a las {hora}\n\n"
        f"_Escribí *menu* para volver al inicio._"
    ))
    # Mantener nombre del negocio
    set_user_state(numero, "estado", "MENU")
    if nombre:
        set_user_state(numero, "nombre_negocio", nombre)


# ═══════════════════════════════════════════════════════════
# FLUJO CANCELAR
# ═══════════════════════════════════════════════════════════

def _flujo_cancel_fecha(numero, texto):
    try:
        fecha = datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        enviar_texto(numero, "❌ Formato inválido. Usá dd/mm/yyyy")
        return

    fecha_str = fecha.strftime("%d/%m/%Y")
    turnos = [t for t in turnos_usuario(numero) if t["fecha"] == fecha_str]

    if not turnos:
        enviar_texto(numero, f"No encontré turnos tuyos para el {fecha_str}.")
        set_user_state(numero, "estado", "MENU")
        return

    set_user_state(numero, "cancel_fecha", fecha_str)
    set_user_state(numero, "estado", "CANCEL_HORA")
    horarios_txt = "\n".join(f"🕐 {t['hora']}" for t in turnos)
    enviar_texto(numero, f"*Tus turnos el {fecha_str}:*\n\n{horarios_txt}\n\n¿Qué hora cancelamos?")


def _flujo_cancel_hora(numero, texto, nombre):
    hora = normalizar_hora(texto)
    if not hora:
        enviar_texto(numero, "❌ Hora inválida.")
        return

    full  = get_full_state(numero)
    fecha = full["datos"].get("cancel_fecha", "")
    ok    = cancelar_turno(numero, fecha, hora)

    if ok:
        enviar_texto(numero, f"✅ Turno del {fecha} a las {hora} cancelado.")
    else:
        enviar_texto(numero, "⚠️ No encontré ese turno.")

    set_user_state(numero, "estado", "MENU")
    if nombre:
        set_user_state(numero, "nombre_negocio", nombre)


# ═══════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════

MENU_ADMIN = (
    "🛠 *ADMIN E-Bot*\n\n"
    "1️⃣  Turnos hoy\n"
    "2️⃣  Próximos turnos\n"
    "3️⃣  Mensajes y leads\n"
    "4️⃣  Bloquear horario\n"
    "5️⃣  Cancelar turno\n"
    "0️⃣  Salir"
)


def _manejar_admin(numero, texto):
    from datetime import date
    hoy = date.today().strftime("%d/%m/%Y")

    if texto == "1":
        turnos = turnos_por_fecha(hoy)
        if not turnos:
            enviar_texto(numero, f"📋 Sin turnos para hoy ({hoy}).")
        else:
            lineas = "\n".join(f"🕐 {t['hora']} — {t['nombre']} ({t['telefono']})" for t in turnos)
            enviar_texto(numero, f"*Turnos hoy {hoy}:*\n\n{lineas}")

    elif texto == "2":
        from storage import obtener_turnos
        todos = obtener_turnos()
        proximos = [
            t for t in todos
            if datetime.strptime(t["fecha"], "%d/%m/%Y").date() >= datetime.now().date()
        ]
        if not proximos:
            enviar_texto(numero, "📋 Sin turnos próximos.")
        else:
            lineas = "\n".join(f"📅 {t['fecha']} {t['hora']} — {t['nombre']}" for t in proximos[:20])
            enviar_texto(numero, f"*Próximos turnos:*\n\n{lineas}")

    elif texto == "3":
        mensajes = obtener_mensajes()
        if not mensajes:
            enviar_texto(numero, "📭 Sin mensajes.")
        else:
            lineas = "\n\n".join(
                f"📱 {m['telefono']} [{m['tipo']}]\n_{m['texto']}_"
                for m in mensajes[:10]
            )
            enviar_texto(numero, f"*Mensajes/Leads:*\n\n{lineas}")

    elif texto == "4":
        set_user_state(numero, "estado", "ADMIN_BLOQUEO_FECHA")
        enviar_texto(numero, "📅 Fecha a bloquear (dd/mm/yyyy):")

    elif texto == "5":
        set_user_state(numero, "estado", "CANCEL_FECHA")
        enviar_texto(numero, "Fecha del turno a cancelar (dd/mm/yyyy):")

    elif texto == "0":
        clear_user(numero)
        enviar_texto(numero, "👋 Saliendo del panel admin.")
    else:
        enviar_texto(numero, MENU_ADMIN)


def _admin_bloqueo(numero, texto, estado):
    if estado == "ADMIN_BLOQUEO_FECHA":
        try:
            fecha = datetime.strptime(texto.strip(), "%d/%m/%Y").date()
        except ValueError:
            enviar_texto(numero, "❌ Formato inválido. Usá dd/mm/yyyy")
            return
        set_user_state(numero, "bloqueo_fecha", fecha.strftime("%d/%m/%Y"))
        set_user_state(numero, "estado", "ADMIN_BLOQUEO_HORA")
        enviar_texto(numero, "🕐 ¿Hora a bloquear? (ej: 10:00) o escribí *todo* para bloquear el día completo:")

    elif estado == "ADMIN_BLOQUEO_HORA":
        full  = get_full_state(numero)
        fecha = full["datos"].get("bloqueo_fecha", "")
        from services import generar_horarios
        if texto.lower() == "todo":
            for h in generar_horarios():
                bloquear_horario(fecha, h, "Admin")
            enviar_texto(numero, f"🔒 Día {fecha} bloqueado completo.")
        else:
            hora = normalizar_hora(texto)
            if not hora:
                enviar_texto(numero, "❌ Hora inválida.")
                return
            bloquear_horario(fecha, hora, "Admin")
            enviar_texto(numero, f"🔒 {fecha} {hora} bloqueado.")
        set_user_state(numero, "estado", "ADMIN_MENU")
        enviar_texto(numero, MENU_ADMIN)
