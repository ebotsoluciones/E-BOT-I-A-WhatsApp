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


# ── MENSAJES DE MARCA ─────────────────────────────────────────────────────────

def msg_bienvenida():
    return (
        f"🤖 *¡Hola! Soy E-Bot*\n"
        f"Automatización inteligente de turnos por WhatsApp.\n\n"
        f"¿Cómo se llama tu negocio o cómo te llamás?\n"
        f"_(Ej: Consultorio Dra. López, Juan, Clínica Central)_"
    )

def msg_bienvenida_demo(nombre_negocio: str):
    return (
        f"🎉 *¡Bienvenido/a, {nombre_negocio}!*\n\n"
        f"Esto es lo que E-Bot puede hacer por vos 👇\n\n"
        f"1️⃣  Turno\n"
        f"2️⃣  Mis turnos\n"
        f"3️⃣  Dejar un mensaje\n"
        f"4️⃣  Urgencia\n"
        f"0️⃣  Salir\n\n"
        f"_Escribí el número o contame qué necesitás._"
    )

def msg_menu(nombre_negocio: str = ""):
    saludo = f"Hola, *{nombre_negocio}* 👋\n\n" if nombre_negocio else ""
    return (
        f"🦙 *E-Bot*\n\n"
        f"{saludo}"
        f"1️⃣  Turno\n"
        f"2️⃣  Mis turnos\n"
        f"3️⃣  Dejar un mensaje\n"
        f"4️⃣  Urgencia\n"
        f"0️⃣  Salir"
    )

def msg_despedida(nombre_negocio: str = ""):
    destinatario = f", *{nombre_negocio}*" if nombre_negocio else ""
    return (
        f"✅ Gracias por probar *E-Bot{destinatario}*\n\n"
        f"📅 Horario de atención: {HORARIO}\n\n"
        f"📞 {TELEFONO}\n"
        f"✉️  {EMAIL}\n"
        f"🌐  {WEB}\n\n"
        f"💬 Escribí *DEMO* para volver a empezar."
    )


# ── PROCESADOR PRINCIPAL ──────────────────────────────────────────────────────

def procesar(numero: str, body: str):
    """
    Punto de entrada. Recibe número (internacional) y texto del mensaje.
    Devuelve None — envía respuesta directamente via whatsapp.py
    """
    texto  = body.strip()
    texto_l = texto.lower()

    full   = get_full_state(numero)
    estado = full["estado"]
    datos  = full["datos"]

    nombre_negocio = datos.get("nombre_negocio", "")

    # ── RESET GLOBAL ──────────────────────────────────────────────────────────
    if texto_l in ["menu", "/start", "demo", "inicio"]:
        clear_user(numero)
        # Si viene con prefijo DEMO:NombreNegocio desde la landing
        if texto_l.startswith("demo:"):
            nombre = texto[5:].strip()
            if nombre:
                set_user_state(numero, "nombre_negocio", nombre)
                set_user_state(numero, "estado", "MENU")
                enviar_texto(numero, msg_bienvenida_demo(nombre))
                return
        # Primer contacto o reset limpio → pedir nombre para personalizar
        set_user_state(numero, "estado", "ESPERANDO_NOMBRE_NEGOCIO")
        enviar_texto(numero, msg_bienvenida())
        return

    # ── PRIMER CONTACTO (estado MENU sin nombre_negocio) ─────────────────────
    if estado == "MENU" and not nombre_negocio:
        set_user_state(numero, "estado", "ESPERANDO_NOMBRE_NEGOCIO")
        enviar_texto(numero, msg_bienvenida())
        return

    # ── CAPTURA NOMBRE NEGOCIO ────────────────────────────────────────────────
    if estado == "ESPERANDO_NOMBRE_NEGOCIO":
        nombre = texto.strip()
        if len(nombre) < 2:
            enviar_texto(numero, "Por favor ingresá un nombre válido (mínimo 2 caracteres).")
            return
        set_user_state(numero, "nombre_negocio", nombre)
        set_user_state(numero, "estado", "MENU")
        enviar_texto(numero, msg_bienvenida_demo(nombre))
        return

    # ── SALIR ─────────────────────────────────────────────────────────────────
    if texto_l in ["0", "salir", "chau", "bye"]:
        enviar_texto(numero, msg_despedida(nombre_negocio))
        clear_user(numero)
        return

    # ── IA EN MENU ────────────────────────────────────────────────────────────
    if estado == "MENU":
        resultado = interpretar_mensaje(body)
        intent    = resultado["intent"]
        mensaje   = resultado["mensaje"]

        if intent == "crear_turno":
            _iniciar_turno(numero, msg)
            return
        elif intent == "ver_turnos":
            _mis_turnos(numero, nombre_negocio)
            return
        elif intent == "cancelar_turno":
            set_user_state(numero, "estado", "CANCEL_FECHA")
            enviar_texto(numero, "Indicá la fecha del turno a cancelar (dd/mm/yyyy):")
            return
        elif intent == "consulta_general" and mensaje:
            enviar_texto(numero, f"🤖 {mensaje}")
            return

        # Fallback menú numérico
        _manejar_menu_numerico(numero, texto, nombre_negocio)
        return

    # ── FLUJOS DE ESTADO ──────────────────────────────────────────────────────

    if estado == "MENSAJE":
        guardar_mensaje("Paciente", numero, body)
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
        _flujo_turno_hora(numero, texto, nombre_negocio)
        return

    if estado == "CANCEL_FECHA":
        _flujo_cancel_fecha(numero, texto)
        return

    if estado == "CANCEL_HORA":
        _flujo_cancel_hora(numero, texto)
        return

    # ── ADMIN ─────────────────────────────────────────────────────────────────
    if estado == "ADMIN_MENU":
        _manejar_admin(numero, texto)
        return

    if estado == "ADMIN_BLOQUEO_FECHA":
        _admin_bloqueo_fecha(numero, texto)
        return

    if estado == "ADMIN_BLOQUEO_HORA":
        _admin_bloqueo_hora(numero, texto)
        return

    # Fallback
    enviar_texto(numero, msg_menu(nombre_negocio))


# ── MENÚ NUMÉRICO PACIENTE ────────────────────────────────────────────────────

def _manejar_menu_numerico(numero, texto, nombre_negocio):
    opciones = {
        "1": lambda: _iniciar_turno(numero),
        "2": lambda: _mis_turnos(numero, nombre_negocio),
        "3": lambda: _iniciar_mensaje(numero),
        "4": lambda: _urgencia(numero),
    }
    accion = opciones.get(texto.strip())
    if accion:
        accion()
    else:
        enviar_texto(numero, msg_menu(nombre_negocio))


def _iniciar_turno(numero):
    set_user_state(numero, "estado", "TURNO_NOMBRE")
    enviar_texto(numero, "👤 ¿Nombre y apellido del paciente?")


def _mis_turnos(numero, nombre_negocio):
    lista = turnos_usuario(numero)
    if not lista:
        enviar_texto(numero, "📋 No tenés turnos próximos registrados.")
    else:
        lineas = "\n".join(f"📅 {t['fecha']} {t['hora']} — {t['nombre']}" for t in lista)
        enviar_texto(numero, f"*Tus turnos:*\n\n{lineas}")


def _iniciar_mensaje(numero):
    set_user_state(numero, "estado", "MENSAJE")
    enviar_texto(numero, "✍️ Escribí tu mensaje y lo registramos:")


def _urgencia(numero):
    enviar_texto(
        numero,
        f"🚨 *Urgencias*\n\nComunicate directamente:\n"
        f"📞 {TELEFONO}\n✉️ {EMAIL}"
    )


# ── FLUJO TURNO ───────────────────────────────────────────────────────────────

def _flujo_turno_fecha(numero, texto):
    try:
        fecha = datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        enviar_texto(numero, "❌ Formato inválido. Usá dd/mm/yyyy (ej: 25/06/2025)")
        return

    if fecha < datetime.now().date():
        enviar_texto(numero, "❌ La fecha ya pasó. Ingresá una fecha futura:")
        return

    fecha_str = fecha.strftime("%d/%m/%Y")
    set_user_state(numero, "turno_fecha", fecha_str)

    libres = horarios_libres(fecha_str)
    if not libres:
        enviar_texto(numero, f"😔 No hay disponibilidad para el {fecha_str}. Probá con otra fecha:")
        return

    set_user_state(numero, "estado", "TURNO_HORA")
    horarios_txt = "\n".join(f"🕐 {h}" for h in libres)
    enviar_texto(numero, f"*Horarios disponibles para {fecha_str}:*\n\n{horarios_txt}\n\n_Respondé con el horario deseado (ej: 10:00)_")


def _flujo_turno_hora(numero, texto, nombre_negocio):
    hora = normalizar_hora(texto)
    if not hora:
        enviar_texto(numero, "❌ Hora inválida. Usá formato HH:MM (ej: 10:00 o 14:30)")
        return

    full  = get_full_state(numero)
    datos = full["datos"]
    fecha = datos.get("turno_fecha", "")
    nombre= datos.get("turno_nombre", "")

    # Verificar que el horario siga libre (puede haberse tomado)
    libres = horarios_libres(fecha)
    if hora not in libres:
        enviar_texto(numero, f"⚠️ El horario {hora} ya no está disponible. Elegí otro:")
        horarios_txt = "\n".join(f"🕐 {h}" for h in libres)
        enviar_texto(numero, horarios_txt)
        return

    agregar_turno(nombre, numero, fecha, hora)
    enviar_texto(
        numero,
        f"✅ *¡Turno confirmado!*\n\n"
        f"👤 {nombre}\n"
        f"📅 {fecha} a las {hora}\n\n"
        f"_Escribí *menu* para volver al inicio._"
    )
    clear_user(numero)
    if nombre_negocio:
        set_user_state(numero, "nombre_negocio", nombre_negocio)
        set_user_state(numero, "estado", "MENU")


# ── FLUJO CANCELAR ────────────────────────────────────────────────────────────

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
    enviar_texto(numero, f"*Tus turnos el {fecha_str}:*\n\n{horarios_txt}\n\n¿Qué hora querés cancelar?")


def _flujo_cancel_hora(numero, texto):
    hora = normalizar_hora(texto)
    if not hora:
        enviar_texto(numero, "❌ Hora inválida.")
        return

    full  = get_full_state(numero)
    fecha = full["datos"].get("cancel_fecha", "")
    nombre_negocio = full["datos"].get("nombre_negocio", "")

    ok = cancelar_turno(numero, fecha, hora)
    if ok:
        enviar_texto(numero, f"✅ Turno del {fecha} a las {hora} cancelado correctamente.")
    else:
        enviar_texto(numero, f"⚠️ No encontré ese turno.")

    set_user_state(numero, "estado", "MENU")
    if nombre_negocio:
        set_user_state(numero, "nombre_negocio", nombre_negocio)


# ── ADMIN ─────────────────────────────────────────────────────────────────────

MENU_ADMIN = (
    "🛠 *ADMIN*\n\n"
    "1️⃣  Turnos hoy\n"
    "2️⃣  Próximos turnos\n"
    "3️⃣  Mensajes recibidos\n"
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
        from datetime import datetime
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
            lineas = "\n\n".join(f"📱 {m['telefono']}\n_{m['texto']}_" for m in mensajes[:10])
            enviar_texto(numero, f"*Mensajes:*\n\n{lineas}")

    elif texto == "4":
        set_user_state(numero, "estado", "ADMIN_BLOQUEO_FECHA")
        enviar_texto(numero, "📅 Fecha a bloquear (dd/mm/yyyy):")

    elif texto == "5":
        set_user_state(numero, "estado", "CANCEL_FECHA")
        enviar_texto(numero, "Indicá la fecha del turno a cancelar (dd/mm/yyyy):")

    elif texto == "0":
        clear_user(numero)
        enviar_texto(numero, "👋 Saliendo del panel admin.")

    else:
        enviar_texto(numero, MENU_ADMIN)


def _admin_bloqueo_fecha(numero, texto):
    try:
        fecha = datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        enviar_texto(numero, "❌ Formato inválido. Usá dd/mm/yyyy")
        return
    set_user_state(numero, "bloqueo_fecha", fecha.strftime("%d/%m/%Y"))
    set_user_state(numero, "estado", "ADMIN_BLOQUEO_HORA")
    enviar_texto(numero, "🕐 ¿Qué hora querés bloquear? (ej: 10:00 / todo para bloquear el día completo)")


def _admin_bloqueo_hora(numero, texto):
    full  = get_full_state(numero)
    fecha = full["datos"].get("bloqueo_fecha", "")

    from services import generar_horarios
    if texto.lower() == "todo":
        for h in generar_horarios():
            bloquear_horario(fecha, h, "Admin")
        enviar_texto(numero, f"🔒 Día {fecha} bloqueado completamente.")
    else:
        hora = normalizar_hora(texto)
        if not hora:
            enviar_texto(numero, "❌ Hora inválida.")
            return
        bloquear_horario(fecha, hora, "Admin")
        enviar_texto(numero, f"🔒 Horario {fecha} {hora} bloqueado.")

    set_user_state(numero, "estado", "ADMIN_MENU")
    enviar_texto(numero, MENU_ADMIN)
