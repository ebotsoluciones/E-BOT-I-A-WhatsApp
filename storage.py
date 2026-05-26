import json
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import DATABASE_URL


@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen. Se llama automáticamente al arrancar."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS turnos (
                id          SERIAL PRIMARY KEY,
                nombre      TEXT NOT NULL,
                telefono    TEXT NOT NULL,
                fecha       TEXT NOT NULL,
                hora        TEXT NOT NULL,
                creado_en   TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS bloqueos (
                id      SERIAL PRIMARY KEY,
                fecha   TEXT NOT NULL,
                hora    TEXT NOT NULL,
                motivo  TEXT DEFAULT '',
                UNIQUE (fecha, hora)
            );

            CREATE TABLE IF NOT EXISTS mensajes (
                id          SERIAL PRIMARY KEY,
                tipo        TEXT NOT NULL,
                telefono    TEXT NOT NULL,
                texto       TEXT NOT NULL,
                creado_en   TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS estados_usuarios (
                telefono    TEXT PRIMARY KEY,
                estado      TEXT DEFAULT 'MENU',
                datos       JSONB DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_turnos_telefono ON turnos(telefono);
            CREATE INDEX IF NOT EXISTS idx_turnos_fecha    ON turnos(fecha);
        """)


# ── ESTADOS DE USUARIO ────────────────────────

def get_user_state(telefono: str, key: str, default=None):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT estado, datos FROM estados_usuarios WHERE telefono = %s",
            (telefono,)
        )
        row = cur.fetchone()
        if not row:
            return default
        if key == "estado":
            return row["estado"]
        return (row["datos"] or {}).get(key, default)


def set_user_state(telefono: str, key: str, value):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT datos, estado FROM estados_usuarios WHERE telefono = %s",
            (telefono,)
        )
        row = cur.fetchone()
        datos  = dict(row["datos"])  if row and row["datos"]  else {}
        estado = row["estado"]       if row and row["estado"] else "MENU"

        if key == "estado":
            estado = value
        else:
            datos[key] = value

        cur.execute("""
            INSERT INTO estados_usuarios (telefono, estado, datos)
            VALUES (%s, %s, %s)
            ON CONFLICT (telefono) DO UPDATE
              SET estado = EXCLUDED.estado,
                  datos  = EXCLUDED.datos
        """, (telefono, estado, json.dumps(datos)))


def clear_user(telefono: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM estados_usuarios WHERE telefono = %s",
            (telefono,)
        )


def get_full_state(telefono: str) -> dict:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT estado, datos FROM estados_usuarios WHERE telefono = %s",
            (telefono,)
        )
        row = cur.fetchone()
        if not row:
            return {"estado": "MENU", "datos": {}}
        return {"estado": row["estado"], "datos": row["datos"] or {}}


# ── TURNOS ────────────────────────────────────

def obtener_turnos():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM turnos ORDER BY fecha, hora")
        return [dict(r) for r in cur.fetchall()]


def agregar_turno(nombre: str, telefono: str, fecha: str, hora: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO turnos (nombre, telefono, fecha, hora)
            VALUES (%s, %s, %s, %s)
        """, (nombre, telefono, fecha, hora))


def cancelar_turno(telefono: str, fecha: str, hora: str) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM turnos
            WHERE telefono = %s AND fecha = %s AND hora = %s
        """, (telefono, fecha, hora))
        return cur.rowcount > 0


def turnos_usuario(telefono: str) -> list:
    from datetime import datetime
    hoy = datetime.now().date()
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM turnos WHERE telefono = %s ORDER BY fecha, hora",
            (telefono,)
        )
        rows = cur.fetchall()
    return [
        dict(r) for r in rows
        if r["fecha"] and
           datetime.strptime(r["fecha"], "%d/%m/%Y").date() >= hoy
    ]


def turnos_por_fecha(fecha: str) -> list:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM turnos WHERE fecha = %s ORDER BY hora",
            (fecha,)
        )
        return [dict(r) for r in cur.fetchall()]


# ── BLOQUEOS ─────────────────────────────────

def bloquear_horario(fecha: str, hora: str, motivo: str = ""):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO bloqueos (fecha, hora, motivo)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (fecha, hora, motivo))


def horario_bloqueado(fecha: str, hora: str) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM bloqueos WHERE fecha = %s AND hora = %s LIMIT 1",
            (fecha, hora)
        )
        return cur.fetchone() is not None


def horarios_libres(fecha: str) -> list:
    from services import generar_horarios
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT hora FROM turnos WHERE fecha = %s", (fecha,))
        turnos_hora = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT hora FROM bloqueos WHERE fecha = %s", (fecha,))
        bloqueos_hora = {r[0] for r in cur.fetchall()}
    ocupados = turnos_hora | bloqueos_hora
    return [h for h in generar_horarios() if h not in ocupados]


# ── MENSAJES ──────────────────────────────────

def guardar_mensaje(tipo: str, telefono: str, texto: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mensajes (tipo, telefono, texto)
            VALUES (%s, %s, %s)
        """, (tipo, telefono, texto))


def obtener_mensajes() -> list:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM mensajes ORDER BY creado_en DESC LIMIT 50")
        return [dict(r) for r in cur.fetchall()]
