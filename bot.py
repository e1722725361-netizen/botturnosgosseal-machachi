import os
import json
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
import pytz
import re
import urllib.request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
PORT = int(os.environ.get("PORT", 8080))
SELF_URL = os.environ.get("SELF_URL", "")  # https://botturnosgosseal-machachi.onrender.com
TZ = pytz.timezone("America/Guayaquil")
DATA_FILE = "data.json"

BASE_MEMBERS = [
    "LUIS PILACUAN",
    "JOSE ALLAICA",
    "RYCHARD TAYPE",
    "LUIS CELLRE",
]

WEEK_ZERO = datetime(2026, 6, 13, tzinfo=TZ)


# ── Auto-ping para no dormirse ─────────────────────────────────────────────────
def keep_alive():
    if not SELF_URL:
        logger.warning("SELF_URL no configurado, el bot puede dormirse en Render Free.")
        return
    while True:
        time.sleep(840)  # cada 14 minutos
        try:
            urllib.request.urlopen(SELF_URL, timeout=10)
            logger.info("Auto-ping OK → %s", SELF_URL)
        except Exception as e:
            logger.warning("Auto-ping falló: %s", e)


# ── Servidor HTTP mínimo ───────────────────────────────────────────────────────
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Turnos Gosseal Machachi - OK")
    def log_message(self, format, *args):
        pass

def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    logger.info("Servidor HTTP en puerto %s", PORT)
    server.serve_forever()


# ── Persistencia ──────────────────────────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"vacations": {}}

def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Lógica de turnos ──────────────────────────────────────────────────────────
def get_week_number(ref: datetime = None) -> int:
    if ref is None:
        ref = datetime.now(TZ)
    return max(0, (ref - WEEK_ZERO).days // 7)

def get_free_index(week: int) -> int:
    return (week + 1) % len(BASE_MEMBERS)

def week_start_date(week: int) -> datetime:
    return WEEK_ZERO + timedelta(weeks=week)

def get_schedule(week: int, data: dict) -> dict:
    now = datetime.now(TZ)
    free_base = BASE_MEMBERS[get_free_index(week)]
    on_vacation = [
        m for m in BASE_MEMBERS
        if m.replace(" ", "_") in data.get("vacations", {})
        and datetime.fromisoformat(data["vacations"][m.replace(" ", "_")]) > now
    ]
    on_duty = [m for m in BASE_MEMBERS if m != free_base and m not in on_vacation]
    free = [free_base] + [m for m in on_vacation if m != free_base]
    return {"on_duty": on_duty, "free": free}

def build_reminder(week: int, data: dict) -> str:
    sched = get_schedule(week, data)
    sat = week_start_date(week)
    sun = sat + timedelta(days=1)
    turno_str = "\n".join(f"  ✅ {m}" for m in sched["on_duty"]) or "  (sin asignar)"
    libre_str = "\n".join(f"  🟡 {m}" for m in sched["free"]) or "  (ninguno)"
    return (
        f"🔔 *RECORDATORIO DE TURNO — Semana #{week}*\n"
        f"📅 *Sábado {sat.strftime('%d/%m/%Y')} y Domingo {sun.strftime('%d/%m/%Y')}*\n\n"
        f"*🔧 DE TURNO:*\n{turno_str}\n\n"
        f"*🟡 LIBRE este fin de semana:*\n{libre_str}\n\n"
        f"_Gosseal Machachi_ 💼"
    )

def find_member(user) -> str | None:
    full = (user.full_name or "").upper()
    uname = (user.username or "").upper()
    for m in BASE_MEMBERS:
        for part in m.split():
            if len(part) > 3 and (part in full or part in uname):
                return m
    return None


# ── Handlers ──────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Bot de Turnos — Gosseal Machachi*\n\n"
        "*Comandos:*\n"
        "• /turno — Turno de este fin de semana\n"
        "• /siguiente — Turno del próximo fin de semana\n"
        "• /calendario — Próximas 8 semanas\n"
        "• /estado — Ver quién está suspendido\n\n"
        "*Para suspenderte escribe:*\n"
        "`suspéndeme 7 días` → fuera 8 días\n"
        "`suspéndeme 15 días` → fuera 16 días\n\n"
        "El sistema te reincorpora automáticamente 🔄",
        parse_mode="Markdown"
    )

async def cmd_turno(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(build_reminder(get_week_number(), data), parse_mode="Markdown")

async def cmd_siguiente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(build_reminder(get_week_number() + 1, data), parse_mode="Markdown")

async def cmd_calendario(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    week = get_week_number()
    lines = ["📅 *CALENDARIO — Próximos 8 fines de semana*\n"]
    for i in range(8):
        w = week + i
        sched = get_schedule(w, data)
        sat = week_start_date(w)
        sun = sat + timedelta(days=1)
        hoy = " ← *ESTE FIN DE SEMANA*" if i == 0 else ""
        lines.append(
            f"*Sem #{w}* — Sáb {sat.strftime('%d/%m')} / Dom {sun.strftime('%d/%m')}{hoy}\n"
            f"  🔧 {', '.join(sched['on_duty']) or 'sin asignar'}\n"
            f"  🟡 Libre: {', '.join(sched['free']) or 'ninguno'}"
        )
    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

async def cmd_estado(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now(TZ)
    activos = {k: v for k, v in data.get("vacations", {}).items()
               if datetime.fromisoformat(v) > now}
    if not activos:
        await update.message.reply_text("✅ Todos activos, nadie suspendido.")
        return
    lines = ["🔴 *Personas suspendidas:*\n"]
    for key, iso in activos.items():
        retorno = datetime.fromisoformat(iso)
        dias = (retorno - now).days + 1
        lines.append(f"  • *{key.replace('_', ' ')}*\n    Regresa: {retorno.strftime('%d/%m/%Y')} (en {dias} día/s)")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    triggers = ["suspéndeme", "suspendeme", "suspéndame", "suspendame"]
    if not any(t in text for t in triggers):
        return
    match = re.search(r"\b(7|15)\b", text)
    if not match:
        await update.message.reply_text(
            "⚠️ Escribe:\n`suspéndeme 7 días` o `suspéndeme 15 días`",
            parse_mode="Markdown"
        )
        return
    dias_fuera = int(match.group(1)) + 1
    member = find_member(update.effective_user)
    if not member:
        await update.message.reply_text("⚠️ No puedo identificarte.")
        return
    data = load_data()
    retorno = datetime.now(TZ) + timedelta(days=dias_fuera)
    data["vacations"][member.replace(" ", "_")] = retorno.isoformat()
    save_data(data)
    await update.message.reply_text(
        f"✅ *{member}* quedas suspendido por *{dias_fuera} días*.\n"
        f"📅 Te reincorporas el *{retorno.strftime('%d/%m/%Y')}*. ¡Descansa! 🏖",
        parse_mode="Markdown"
    )

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID:
        return
    data = load_data()
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=build_reminder(get_week_number(), data),
        parse_mode="Markdown"
    )
    logger.info("Recordatorio enviado — semana #%s", get_week_number())


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if not TOKEN:
        raise ValueError("Falta BOT_TOKEN en variables de entorno")

    # Servidor HTTP
    threading.Thread(target=run_http_server, daemon=True).start()

    # Auto-ping para no dormirse
    threading.Thread(target=keep_alive, daemon=True).start()

    # Construir la aplicación de Telegram
    app = Application.builder().token(TOKEN).build()

    # Registrar handlers de comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("turno", cmd_turno))
    app.add_handler(CommandHandler("siguiente", cmd_siguiente))
    app.add_handler(CommandHandler("calendario", cmd_calendario))
    app.add_handler(CommandHandler("estado", cmd_estado))

    # Handler para mensajes de texto (detección de "suspéndeme")
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Job semanal: enviar recordatorio cada viernes a las 18:00 (hora Guayaquil)
    app.job_queue.run_daily(
        send_reminder,
        time=datetime.strptime("18:00", "%H:%M").time().replace(tzinfo=TZ),
        days=(4,),  # 0=lunes ... 4=viernes
        name="recordatorio_semanal"
    )

    logger.info("Bot iniciado, escuchando...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
