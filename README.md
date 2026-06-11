# 🤖 Bot de Turnos — Gosseal Machachi

Bot de Telegram para gestionar los turnos semanales del equipo de 4 personas.

## 👥 Equipo

| Nombre | Turno semana 1 |
|---|---|
| LUIS PILACUAN | ✅ De turno |
| JOSE ALLAICA | 🟡 Libre |
| RYCHARD TAYPE | ✅ De turno |
| LUIS CELLRE | ✅ De turno |

> La semana 0 comienza el **sábado 14 de junio de 2025**.  
> Cada semana **rota** quién queda libre: semana 0 → JOSE, semana 1 → RYCHARD, semana 2 → LUIS CELLRE, semana 3 → LUIS PILACUAN, y así infinitamente.

---

## ⚙️ Configuración en Render

### 1. Crear el bot en Telegram
1. Abre Telegram y busca `@BotFather`
2. Escribe `/newbot`
3. Ponle el nombre: **botturnosgosseal-machachi**
4. Copia el **TOKEN** que te da

### 2. Obtener el CHAT_ID del grupo
1. Agrega el bot al grupo de Telegram donde quieres los recordatorios
2. Escribe cualquier mensaje en el grupo
3. Abre en el navegador:  
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
4. Busca `"chat":{"id":` — ese número es tu `CHAT_ID`  
   *(si el grupo tiene número negativo como `-100123456`, cópialo con el guion)*

### 3. Subir a GitHub
```bash
git init
git add .
git commit -m "Bot turnos Gosseal Machachi"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/botturnosgosseal-machachi.git
git push -u origin main
```

### 4. Desplegar en Render
1. Ve a [render.com](https://render.com) → **New → Blueprint** (o New → Background Worker)
2. Conecta tu repo de GitHub
3. En **Environment Variables** agrega:
   - `BOT_TOKEN` = el token de BotFather
   - `CHAT_ID` = el ID del grupo
4. Haz clic en **Deploy**

---

## 💬 Comandos del bot

| Comando | Descripción |
|---|---|
| `/start` | Muestra ayuda |
| `/turno` | Ver turno de esta semana |
| `/siguiente` | Ver turno de la próxima semana |
| `/calendario` | Ver las próximas 8 semanas |
| `/vacaciones` | Instrucciones para salir del turno |
| `/estado` | Ver quién está de vacaciones |

---

## 🏖 Sistema de vacaciones

Escribe en el chat (sin comando):

```
inhabilítame 7 días
```
→ El bot te saca **8 días** del turno y te reincorpora automáticamente.

```
inhabilítame 15 días
```
→ El bot te saca **16 días** del turno.

```
inhabilítame vacaciones
```
→ El bot te saca **16 días** (vacaciones completas).

---

## 📅 Recordatorios automáticos

Cada **viernes** el bot manda automáticamente **3 recordatorios** al grupo:
- ⏰ 08:00 AM (hora Ecuador)
- ⏰ 01:00 PM
- ⏰ 07:00 PM

---

## 🗂 Archivos

```
botturnosgosseal-machachi/
├── bot.py           # Código principal del bot
├── requirements.txt # Dependencias Python
├── render.yaml      # Configuración de Render
├── data.json        # (se crea automático) Vacaciones guardadas
└── README.md        # Esta guía
```
