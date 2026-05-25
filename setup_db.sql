-- ============================================================
-- E-Bot Soluciones — Setup de base de datos PostgreSQL/Supabase
-- Ejecutar una sola vez en el SQL Editor de Supabase
-- ============================================================

CREATE TABLE IF NOT EXISTS turnos (
    id          SERIAL PRIMARY KEY,
    nombre      TEXT NOT NULL,
    telefono    TEXT NOT NULL,
    fecha       TEXT NOT NULL,        -- formato dd/mm/yyyy
    hora        TEXT NOT NULL,        -- formato HH:MM
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
    tipo        TEXT NOT NULL,        -- 'Paciente' | 'Admin'
    telefono    TEXT NOT NULL,
    texto       TEXT NOT NULL,
    creado_en   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS estados_usuarios (
    telefono    TEXT PRIMARY KEY,
    estado      TEXT DEFAULT 'MENU',
    datos       JSONB DEFAULT '{}'
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_turnos_telefono ON turnos(telefono);
CREATE INDEX IF NOT EXISTS idx_turnos_fecha    ON turnos(fecha);
CREATE INDEX IF NOT EXISTS idx_mensajes_fecha  ON mensajes(creado_en DESC);
