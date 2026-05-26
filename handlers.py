from datetime import datetime

from storage import (
    get_full_state, set_user_state, clear_user,
    turnos_usuario, agregar_turno, cancelar_turno,
    horarios_libres, guardar_mensaje,
    bloquear_horario, turnos_por_fecha, obtener_mensajes
)
from services  import normalizar_hora
from ia        import interpretar_mensaje
from whatsapp  import (
    enviar_texto, reenviar_a_numero,
    enviar_imagen_con_botones, enviar_interactivo_botones
)
from config    import ADMINS, MODO_TEST, MARCA, TELEFONO, EMAIL, WEB, HORARIO

NUMERO_ASESOR = "5492494510525"
LOGO_URL      = "https://raw.githubusercontent.com/ebotsoluciones/ebotsoluciones-web/main/logo.png"

# ═══════════════════════════════════════════════════════════
# MENSAJES
# ═══════════════════════════════════════════════════════════

MSG_PRESENTACION = (
    "🤖 *Probá el DEMO con I.A.*\n\n"
    "✅ Turnos automáticos 24/7\n"
    "✅ Sin llamadas ni confusiones\n"
    "✅ Recordatorios automáticos\n\n"
    "¿Qué querés hacer?\n\n"
    "1️⃣  Ver *DEMO* personalizada\n"
    "2️⃣  Hablar con un *asesor*"
)

MSG_PEDIR_NOMBRE = (
    "🎯 *¡Genial! Vamos a personalizar tu demo.*\n\n"
    "¿Cómo se llama tu negocio?\n"
    "_(Ej: Consultorio Dra. López, Estudio Barlovento)_"
)

MSG_ASESOR = (
    "💬 *¡Con gusto te contactamos!*\n\n"
    "Escribí tu *nombre*, *consulta* y *teléfono* y te respondemos a la brevedad 👇"
)

PALABRAS_SALIR = ["0", "salir", "chau", "bye", "adios", "adiós", "hasta luego", "nos vemos"]
PALABRAS_URGENCIA = ["urgencia", "urgente", "emergencia"]
PALABRAS_MENSAJE = ["mensaje", "dejar mensaje", "quiero dejar un mensaje", "mandar mensaje"]


def enviar_presentacion(numero: str):
    ok = enviar_imagen_con_botones(
        numero=numero,
        imagen_url=LOGO_URL,
        body=(
            "🤖 *Probá el DEMO con I.A.*\n\n"
            "✅ Turnos automáticos 24/7\n"
            "✅ Sin llamadas ni confusiones\n"
            "✅ Recordatorios automáticos"
        ),
        footer="ebotsoluciones.lat",
        botones=[
            {"id": "btn_demo",   "title": "🚀 Ver DEMO"},
            {"id": "btn_asesor", "title": "💬 Hablar con asesor"},
        ]
    )
    if not ok:
        enviar_texto(numero, MSG_PRESENTACION)


def _menu_texto(nombre):
    return (
        f"🦙 *E-Bot*  ·  _{nombre}_ 🤖\n\n"
        f"1️⃣  Sacar un turno\n"
        f"2️⃣  Ver mis turnos\n"
        f"3️⃣  Dejar un mensaje\n"
        f"4️⃣  Urgencia\n"
        f"0️⃣  Salir\n\n"
        f"_Escribí el número o contame qué necesitás._"
    )


def _msg_bienvenida_demo(nombre):
    return (
        f"🎉 *¡Bienvenido/a, {nombre}!*\n\n"
        f"Esto es lo que E-Bot puede hacer 👇\n\n"
        f"1️⃣  Sacar un turno\n"
        f"2️⃣  Ver mis turnos\n"
        f"3️⃣  Dejar un mensaje\n"
        f"4️⃣  Urgencia\n"
        f"0️⃣  Salir\n\n"
        f"_Escribí el número o contame qué necesitás._ 🤖"
    )


def enviar_cierre_demo(numero: str, nombre: str):
    nombre_fmt = f"*{nombre}*" if nombre else "E-Bot"
    ok = enviar_interactivo_botones(
        numero=numero,
        header_text="🚀 ¿Te convenciste?",
        body=(
            f"Gracias por probar E-Bot, {nombre_fmt} 🎉\n\n"
            f"Implementamos el sistema en tu negocio en *48hs*.\n\n"
            f"¿Qué querés hacer?"
        ),
        footer="ebotsoluciones.lat",
        botones=[
            {"id": "btn_contactar", "title": "📞 Quiero que me contacten"},
            {"id": "btn_pregunta",  "title": "❓ Tengo una pregunta"},
            {"id": "btn_volver",    "title": "🔄 Seguir probando"},
        ]
    )
    if not ok:
        enviar_texto(numero, (
            f"✅ Gracias por probar E-Bot, {nombre_fmt} 🎉\n\n"
            f"Implementamos el sistema en *48hs*.\n\n"
            f"1️⃣  Quiero que me contacten\n"
            f"2️⃣  Tengo una pregunta\n"
            f"3️⃣  Seguir probando\n\n"
            f"✉️ {EMAIL}\n🌐 {WEB}"
        ))


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

    # ── ADMIN ─────────────────────────────────────────────────
    numero_limpio = numero.replace("whatsapp:", "").replace("+", "")
    if numero_limpio in ADMINS or (MODO_TEST and texto_l == "adm"):
        if texto_l == "adm" and estado != "ADMIN_MENU":
            set_user_state(numero, "estado", "ADMIN_MENU")
            enviar_texto(numero, MENU_ADMIN)
            return
        if estado == "ADMIN_MENU":
            _manejar_admin(numero, texto)
            return
        if estado in ("ADMIN_BLOQUEO_FECHA", "ADMIN_BLOQUEO_HORA"):
            _admin_bloqueo(numero, texto, estado)
            return

    # ── RESET ─────────────────────────────────────────────────
    if texto_l in ["hola", "menu", "/start", "inicio", "reiniciar", "demo"]:
        clear_user(numero)
        enviar_presentacion(numero)
        set_user_state(numero, "estado", "FUNNEL_INICIO")
        return

    # ── PRIMER CONTACTO ───────────────────────────────────────
    if estado == "MENU" and not nombre:
        enviar_presentacion(numero)
        set_user_state(numero, "estado", "FUNNEL_INICIO")
        return

    # ── FUNNEL: ELECCIÓN ──────────────────────────────────────
    if estado == "FUNNEL_INICIO":
        if texto_l in ["1", "demo", "ver demo", "quiero demo", "btn_demo", "🚀 ver demo"]:
            set_user_state(numero, "estado", "FUNNEL_PEDIR_NOMBRE")
            enviar_texto(numero, MSG_PEDIR_NOMBRE)
        elif texto_l in ["2", "asesor", "hablar", "contacto", "btn_asesor", "💬 hablar con asesor"]:
            set_user_state(numero, "estado", "FUNNEL_ASESOR_MSG")
            enviar_texto(numero, MSG_ASESOR)
        else:
            enviar_texto(numero, "Respondé *1* para ver la DEMO o *2* para hablar con un asesor.")
        return

    # ── FUNNEL: CAPTURA NOMBRE ────────────────────────────────
    if estado == "FUNNEL_PEDIR_NOMBRE":
        if len(texto.strip()) < 2:
            enviar_texto(numero, "Por favor ingresá un nombre válido.")
            return
        nombre_nuevo = texto.strip()
        set_user_state(numero, "nombre_negocio", nombre_nuevo)
        set_user_state(numero, "estado", "MENU")
        enviar_texto(numero, _msg_bienvenida_demo(nombre_nuevo))
        return

    # ── FUNNEL: MENSAJE AL ASESOR ─────────────────────────────
    if estado == "FUNNEL_ASESOR_MSG":
        guardar_mensaje("Lead", numero, texto)
        reenviar_a_numero(
            NUMERO_ASESOR, numero,
            f"{texto}\n\n_Desde: {numero}_"
        )
        enviar_texto(numero, (
            "✅ *¡Mensaje recibido!*\n\n"
            "Un asesor te va a contactar pronto.\n\n"
            f"✉️ {EMAIL}\n🌐 {WEB}\n\n"
            "_Escribí *hola* para volver al inicio._"
        ))
        set_user_state(numero, "estado", "MENU")
        if nombre:
            set_user_state(numero, "nombre_negocio", nombre)
        return

    # ── CIERRE DEMO ───────────────────────────────────────────
    if estado == "FUNNEL_CIERRE":
        if texto_l in ["1", "btn_contactar", "quiero que me contacten"]:
            set_user_state(numero, "estado", "FUNNEL_ASESOR_MSG")
            enviar_texto(numero, "✍️ Dejanos tu *nombre*, *consulta* y *teléfono*:")
        elif texto_l in ["2", "btn_pregunta", "tengo una pregunta"]:
            set_user_state(numero, "estado", "FUNNEL_ASESOR_MSG")
            enviar_texto(numero, "✍️ Escribí tu *pregunta* y *teléfono* para contactarte:")
        elif texto_l in ["3", "btn_volver", "seguir", "volver"]:
            set_user_state(numero, "estado", "MENU")
            enviar_texto(numero, _menu_texto(nombre))
        else:
            enviar_cierre_demo(numero, nombre)
        return

    # ── SALIR ─────────────────────────────────────────────────
    if texto_l in PALABRAS_SALIR:
        enviar_cierre_demo(numero, nombre)
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

    # ── MENÚ PRINCIPAL (con IA) ───────────────────────────────
    if estado == "MENU":
        _procesar_menu(numero, texto, body, nombre)
        return

    # Fallback
    if nombre:
        enviar_texto(numero, _menu_texto(nombre))
    else:
        enviar_presentacion(numero)
        set_user_state(numero, "estado", "FUNNEL_INICIO")


# ═══════════════════════════════════════════════════════════
# MENÚ CON IA
# ═══════════════════════════════════════════════════════════

def _procesar_menu(numero, texto, body_original, nombre):
    # Numérico primero
    if texto.strip() in ["1", "2", "3", "4", "0"]:
        _menu_numerico(numero, texto.strip(), nombre)
        return

    # Salir por texto
    if texto.lower() in PALABRAS_SALIR:
        enviar_cierre_demo(numero, nombre)
        set_user_state(numero, "estado", "FUNNEL_CIERRE")
        return

    # Urgencia directa
    if any(w in texto.lower() for w in PALABRAS_URGENCIA):
        enviar_texto(numero, f"🚨 *Urgencias*\n\n📞 {TELEFONO}\n✉️ {EMAIL}")
        enviar_texto(numero, _menu_texto(nombre))
        return

    # Mensaje directo
    if any(w in texto.lower() for w in PALABRAS_MENSAJE):
        set_user_state(numero, "estado", "MENSAJE")
        enviar_texto(numero, "✍️ Escribí tu mensaje y lo registramos:")
        return

    # IA para el resto
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
    elif intent == "consulta_general":
        if any(w in body_original.lower() for w in PALABRAS_URGENCIA):
            enviar_texto(numero, f"🚨 *Urgencias*\n\n📞 {TELEFONO}\n✉️ {EMAIL}")
        elif mensaje:
            enviar_texto(numero, f"🤖 {mensaje}")
        enviar_texto(numero, _menu_texto(nombre))
    else:
        enviar_texto(numero, _menu_texto(nombre))


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
    elif opcion == "0":
        enviar_cierre_demo(numero, nombre)
        set_user_state(numero, "estado", "FUNNEL_CIERRE")


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
        enviar_texto(numero, "❌ Formato inválido. Usá dd/mm/yyyy (ej: 27/05/2026)")
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
        enviar_texto(numero, "❌ Hora inválida. Usá HH:MM (ej: 10:00 o 14)")
        return

    full  = get_full_state(numero)
    datos = full["datos"]
    fecha = datos.get("turno_fecha", "")
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

    enviar_texto(numero, f"✅ Turno del {fecha} a las {hora} cancelado." if ok else "⚠️ No encontré ese turno.")
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
        enviar_texto(numero, "🕐 ¿Hora a bloquear? (ej: 10:00) o *todo* para bloquear el día:")

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
