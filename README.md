# 🤖 E-Bot I.A — WhatsApp Cloud API + PostgreSQL

**E-Bot Soluciones** | Córdoba, Argentina
🌐 [ebotsoluciones.lat](https://ebotsoluciones.lat/) | ✉️ contacto@ebotsoluciones.lat

---

## ¿Qué es E-Bot I.A?

Bot de WhatsApp para gestión automática de turnos con IA, sin Twilio.

- 📅 Agenda turnos con lenguaje natural
- ❌ Cancela turnos
- 📋 Consulta disponibilidad
- 🤖 IA interpreta intención del usuario
- 🎨 Demo personalizado con nombre del negocio
- 🛠 Panel admin por WhatsApp

---

## Arquitectura

```
app.py          → Webhook Flask (WhatsApp Cloud API)
handlers.py     → Lógica de flujo y estados
services.py     → Reglas de horarios
storage.py      → PostgreSQL (Supabase/Railway)
whatsapp.py     → Envío de mensajes via Meta API
ia.py           → Interpretación con OpenAI
config.py       → Variables de entorno
```

---

## Stack

| Componente     | Tecnología               |
|---------------|--------------------------|
| Mensajería    | WhatsApp Cloud API (Meta)|
| Backend       | Python + Flask           |
| Base de datos | PostgreSQL (Supabase)    |
| IA            | OpenAI gpt-4o-mini       |
| Deploy        | Railway                  |

---

## Setup rápido

### 1. Clonar y dependencias

```bash
git clone https://github.com/ebotsoluciones/E-BOT-I-A.git
cd E-BOT-I-A
pip install -r requirements.txt
```

### 2. Variables de entorno (.env)

```env
# WhatsApp Cloud API
WA_TOKEN=EAAxxxxxxxx
WA_PHONE_ID=1234567890
WA_VERIFY_TOKEN=ebot_verify

# Base de datos
DATABASE_URL=postgresql://user:pass@host:5432/db

# OpenAI
OPENAI_API_KEY=sk-...

# Opcional
MODO_TEST=true
ADMINS=5493515000000,5493516000000
WA_DISPLAY_NUMBER=+54 351 XXX XXXX
```

### 3. Crear tablas en Supabase

Ejecutar `setup_db.sql` en el SQL Editor de Supabase.

### 4. Configurar webhook en Meta

- URL: `https://tu-dominio.railway.app/webhook`
- Verify Token: el mismo que `WA_VERIFY_TOKEN`
- Suscribirse a: `messages`

### 5. Correr

```bash
python app.py
# o en producción:
gunicorn app:app
```

---

## Flujo demo

```
Usuario escribe cualquier cosa
        ↓
Bot pide nombre del negocio
        ↓
Usuario: "Clínica San Marcos"
        ↓
Bot: "¡Bienvenido, Clínica San Marcos! Esto es lo que puedo hacer..."
        ↓
Menú → Turno / Mis turnos / Mensaje / Urgencia / Salir
        ↓
Al salir → Despedida con datos de E-Bot Soluciones
```

---

## Landing web

`ebot_landing.html` — Página de perfil estilo WhatsApp Business con:
- Logo E-Bot Soluciones
- Botón "DEMO personalizado" (abre modal, pide nombre, abre WhatsApp con `DEMO:nombre`)
- Botón "Mensaje a E-Bot Soluciones"

**Importante:** reemplazar `WA_NUMBER` en el HTML con tu número real.

---

## Panel admin

Acceso: escribir `adm` desde un número registrado en `ADMINS`.

| Opción | Función              |
|--------|----------------------|
| 1      | Turnos hoy           |
| 2      | Próximos turnos      |
| 3      | Mensajes recibidos   |
| 4      | Bloquear horario     |
| 5      | Cancelar turno       |

---

## Licencia

Uso privado / comercial — E-Bot Soluciones.
