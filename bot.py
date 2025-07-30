import asyncio
import json
import random
import os
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# === BOT CONFIG ===
BOT_TOKEN = "8387365932:AAGmMO0h2TVNE-bKpHME22sqWApfm7_UW6c"
ADMIN_ID = 5480597971  # Replace with your admin ID

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# === DATA STORAGE ===
DATA_FILE = "data.json"
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)
DATA = {"users": {}}

def load_data():
    global DATA
    try:
        with open(DATA_FILE, "r") as f:
            DATA = json.load(f)
    except FileNotFoundError:
        DATA = {"users": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(DATA, f)
    # keep only 3 backups
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(BACKUP_DIR, f"data_{ts}.json"), "w") as f:
        json.dump(DATA, f)
    backups = sorted(os.listdir(BACKUP_DIR))
    if len(backups) > 3:
        os.remove(os.path.join(BACKUP_DIR, backups[0]))

# === LANGUAGES ===
LANGS = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}
TEXTS = {
    "en": {
        "welcome": "👋 Welcome to <b>Smart Daily Planner</b>!\nChoose your language:",
        "intro": "✅ <b>What can I do?</b>\n• ➕ Add Task – add tasks\n• 📋 List Tasks – view all tasks\n• ✅ Mark Done – mark tasks as done\n• 📊 Daily Report – see stats\n• 👤 Profile – view XP & streak\n• 🏆 Leaderboard – top users\n💡 Use /help anytime!",
        "help": "💡 <b>Help</b>: Complete tasks to earn XP, keep streaks alive and climb ranks!",
        "no_tasks": "📭 You have no tasks.",
        "task_added": "🆕 Task added: {}",
        "task_done": "✅ Task completed: {}\n⭐ +3 XP",
        "invalid_number": "❌ Invalid task number.",
        "profile": "👤 <b>Profile</b>\nID: <code>{}</code>\nName: {}\nCompleted: {}\nStreak: {} days\nXP: {} ({})",
        "report": "📊 <b>Daily Report</b>\n✅ Completed: {}\n📌 Pending: {}\n🎯 Completion: {}%\n⭐ XP: {}\n🔥 {}",
        "leaderboard": "🏆 <b>Leaderboard</b>\n{}"
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в <b>Smart Daily Planner</b>!\nВыберите язык:",
        "intro": "✅ <b>Что я могу?</b>\n• ➕ Add Task – добавить задачу\n• 📋 List Tasks – список задач\n• ✅ Mark Done – отметить выполненной\n• 📊 Daily Report – статистика\n• 👤 Profile – XP и серия\n• 🏆 Leaderboard – топ пользователей\n💡 Используйте /help в любое время!",
        "help": "💡 <b>Помощь</b>: Выполняйте задачи, получайте XP, сохраняйте серии и повышайте ранг!",
        "no_tasks": "📭 У вас нет задач.",
        "task_added": "🆕 Задача добавлена: {}",
        "task_done": "✅ Задача выполнена: {}\n⭐ +3 XP",
        "invalid_number": "❌ Неверный номер задачи.",
        "profile": "👤 <b>Профиль</b>\nID: <code>{}</code>\nИмя: {}\nВыполнено: {}\nСерия: {} дней\nXP: {} ({})",
        "report": "📊 <b>Отчет</b>\n✅ Выполнено: {}\n📌 В ожидании: {}\n🎯 Завершено: {}%\n⭐ XP: {}\n🔥 {}",
        "leaderboard": "🏆 <b>Топ пользователей</b>\n{}"
    }
}

MOTIVATIONS = [
    "🔥 Keep pushing, you’re doing amazing!",
    "💪 Small steps every day lead to big success.",
    "🚀 You’re on your way to greatness, keep going!",
    "🌟 Consistency beats motivation. Stay consistent!",
    "🏆 Every completed task is a victory. Well done!"
]
TIPS = [
    "💡 Tip: Use deadlines to stay focused.",
    "💡 Tip: Check profile daily to track progress.",
    "💡 Tip: Complete at least 80% tasks to keep streak."
]

# === KEYBOARD ===
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("➕ Add Task"), KeyboardButton("📋 List Tasks")],
            [KeyboardButton("✅ Mark Done"), KeyboardButton("📊 Daily Report")],
            [KeyboardButton("👤 Profile"), KeyboardButton("🏆 Leaderboard")]
        ], resize_keyboard=True
    )

# === XP & RANKS ===
def rank(xp):
    if xp < 200: return "🎯 Rookie"
    if xp < 500: return "⚡ Achiever"
    if xp < 1200: return "🔥 Crusher"
    if xp < 2500: return "🏆 Master"
    return "🌟 Legend"

def add_xp(uid, amount):
    DATA["users"][uid]["xp"] += amount

# === HANDLERS ===

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    uid = str(message.from_user.id)
    if uid not in DATA["users"]:
        DATA["users"][uid] = {"lang": "en", "name": None, "tasks": [], "completed": 0, "xp": 0, "streak": 0, "last_active": ""}
        save_data()
    await message.answer(TEXTS["en"]["welcome"] + "\n" + "\n".join([f"{v}" for v in LANGS.values()]))

@dp.message(F.text.in_(LANGS.values()))
async def set_language(message: Message):
    uid = str(message.from_user.id)
    lang = "ru" if "Russian" in message.text or "Рус" in message.text else "en"
    DATA["users"][uid]["lang"] = lang
    save_data()
    await message.answer("✍️ Send me your nickname to register:")

@dp.message(F.text.regexp("^[A-Za-z0-9_]{2,20}$"))
async def set_nickname(message: Message):
    uid = str(message.from_user.id)
    if DATA["users"][uid]["name"] is None:
        DATA["users"][uid]["name"] = message.text
        save_data()
        await message.answer(f"✅ Registered as <b>{message.text}</b>!", reply_markup=main_kb())
        await message.answer(TEXTS[DATA["users"][uid]["lang"]]["intro"])
    else:
        await message.answer("ℹ️ You are already registered.", reply_markup=main_kb())

@dp.message(F.text == "/help")
async def help_cmd(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    await message.answer(TEXTS[lang]["help"])

@dp.message(F.text == "➕ Add Task")
async def ask_task(message: Message):
    DATA["users"][str(message.from_user.id)]["adding"] = True
    await message.answer("✍️ Send me the task:")

@dp.message(F.text == "📋 List Tasks")
async def list_tasks(message: Message):
    u = DATA["users"][str(message.from_user.id)]
    lang = u["lang"]
    if not u["tasks"]:
        await message.answer(TEXTS[lang]["no_tasks"])
    else:
        await message.answer("📝 Tasks:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(u["tasks"])]))

@dp.message(F.text == "✅ Mark Done")
async def ask_done(message: Message):
    u = DATA["users"][str(message.from_user.id)]
    if not u["tasks"]:
        await message.answer(TEXTS[u["lang"]]["no_tasks"])
        return
    await message.answer("Send task number to mark as done:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(u["tasks"])]))

@dp.message(F.text == "📊 Daily Report")
async def manual_report(message: Message):
    await send_report(str(message.from_user.id))

@dp.message(F.text == "👤 Profile")
async def profile(message: Message):
    u = DATA["users"][str(message.from_user.id)]
    lang = u["lang"]
    await message.answer(TEXTS[lang]["profile"].format(u["user_id"], u["name"], u["completed"], u["streak"], u["xp"], rank(u["xp"])))

@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    lb = sorted(DATA["users"].values(), key=lambda x: x["xp"], reverse=True)[:10]
    text = "\n".join([f"{i+1}. {u['name']} – {u['xp']} XP ({rank(u['xp'])})" for i, u in enumerate(lb)])
    await message.answer(TEXTS[lang]["leaderboard"].format(text))

@dp.message(F.text.startswith("/stats"))
async def stats_cmd(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"👥 Total users: {len(DATA['users'])}")

@dp.message(F.text.startswith("/backup"))
async def backup_cmd(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer_document(open(DATA_FILE, "rb"))

@dp.message()
async def catch_all(message: Message):
    uid = str(message.from_user.id)
    u = DATA["users"].get(uid)
    if not u:
        return
    # Ignore /commands
    if message.text.startswith("/"):
        return
    # Handle task adding
    if u.get("adding"):
        u["tasks"].append(message.text)
        u["adding"] = False
        save_data()
        await message.answer(TEXTS[u["lang"]]["task_added"].format(message.text))
        return
    # Handle marking done
    if message.text.isdigit():
        idx = int(message.text) - 1
        if 0 <= idx < len(u["tasks"]):
            task = u["tasks"].pop(idx)
            u["completed"] += 1
            add_xp(uid, 3)
            save_data()
            await message.answer(TEXTS[u["lang"]]["task_done"].format(task))
        else:
            await message.answer(TEXTS[u["lang"]]["invalid_number"])

# === REPORT FUNCTION ===
async def send_report(uid):
    u = DATA["users"][uid]
    lang = u["lang"]
    total = len(u["tasks"])
    completed = u["completed"]
    percent = int((completed/(completed+total))*100) if completed+total>0 else 0
    msg = TEXTS[lang]["report"].format(completed, total, percent, u["xp"], random.choice(MOTIVATIONS))
    if random.random() < 0.3:
        msg += "\n" + random.choice(TIPS)
    await bot.send_message(uid, msg)

# === SCHEDULED DAILY REPORTS ===
async def scheduled_reports():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        if datetime.now(tz).strftime("%H:%M") == "21:00":
            for uid in DATA["users"]:
                await send_report(uid)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# === MAIN ===
async def main():
    load_data()
    asyncio.create_task(scheduled_reports())
    print("✅ Bot is running!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
