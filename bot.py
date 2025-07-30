import asyncio
import json
import random
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# --- BOT CONFIG ---
BOT_TOKEN = "8387365932:AAGmMO0h2TVNE-bKpHME22sqWApfm7_UW6c"
ADMIN_ID = 5480597971

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# --- FILE STORAGE ---
DATA_FILE = "data.json"
DATA = {"users": {}}

# --- LANGUAGES ---
LANGS = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}

TEXTS = {
    "en": {
        "welcome": "👋 Welcome to <b>Smart Daily Planner</b>!\n\n"
                   "🔥 I help you stay productive with tasks, streaks, XP, and daily reports.\n"
                   "✅ Choose your language to start!",
        "intro": "📚 <b>What can I do?</b>\n"
                 "• ➕ Add Task → add new task\n"
                 "• 📋 List Tasks → view tasks\n"
                 "• ✅ Mark Done → mark task completed\n"
                 "• 📊 Daily Report → see your stats\n"
                 "• 👤 Profile → view streak, XP, rank\n"
                 "💡 Stay consistent and win streak bonuses!",
        "help": "💡 Commands:\n/start – restart bot\n/help – show help\n/stats – admin only",
        "profile": "👤 <b>Profile</b>\n🆔 ID: <code>{}</code>\n🏷️ Name: {}\n✅ Completed: {}\n🔥 Streak: {} days\n⭐ XP: {} ({})",
        "no_tasks": "📭 You have no tasks.",
        "task_added": "🆕 Task added: {}",
        "task_done": "✅ Task completed: {}",
        "invalid_number": "❌ Invalid task number.",
        "report": "📊 <b>Daily Report</b>\n✅ Completed: {}\n📌 Pending: {}\n🎯 Completion: {}%\n{}\n\n💡 {}",
        "streak_lost": "❌ Streak lost today. Try hitting 80% tomorrow!",
        "streak_ok": "🔥 Streak maintained! Keep going!"
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в <b>Smart Daily Planner</b>!\n\n"
                   "🔥 Я помогу вам оставаться продуктивными: задачи, серии, XP, отчеты.\n"
                   "✅ Выберите язык для начала!",
        "intro": "📚 <b>Что я умею?</b>\n"
                 "• ➕ Add Task → добавить задачу\n"
                 "• 📋 List Tasks → список задач\n"
                 "• ✅ Mark Done → завершить задачу\n"
                 "• 📊 Daily Report → ваш отчет\n"
                 "• 👤 Profile → streak, XP, ранг\n"
                 "💡 Будьте постоянны и получайте бонусы!",
        "help": "💡 Команды:\n/start – перезапуск\n/help – помощь\n/stats – только для админа",
        "profile": "👤 <b>Профиль</b>\n🆔 ID: <code>{}</code>\n🏷️ Имя: {}\n✅ Выполнено: {}\n🔥 Серия: {} дней\n⭐ XP: {} ({})",
        "no_tasks": "📭 У вас нет задач.",
        "task_added": "🆕 Задача добавлена: {}",
        "task_done": "✅ Задача выполнена: {}",
        "invalid_number": "❌ Неверный номер задачи.",
        "report": "📊 <b>Отчет</b>\n✅ Выполнено: {}\n📌 В ожидании: {}\n🎯 Завершено: {}%\n{}\n\n💡 {}",
        "streak_lost": "❌ Серия прервана. Попробуйте завтра!",
        "streak_ok": "🔥 Серия продолжается! Отлично!"
    }
}

# --- MOTIVATIONS & RANKS ---
MOTIVATIONS = [
    "🔥 Keep pushing, you’re doing amazing!",
    "💪 Small steps every day lead to big success.",
    "🚀 You’re on your way to greatness, keep going!",
    "🌟 Consistency beats motivation. Stay consistent!",
    "🏆 Every completed task is a victory. Well done!"
]

def rank(xp):
    if xp < 200: return "🎯 Rookie"
    if xp < 500: return "⚡ Achiever"
    if xp < 1200: return "🔥 Crusher"
    if xp < 2500: return "🏆 Master"
    return "🌟 Legend"

# --- SAVE / LOAD ---
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

# --- MIGRATION: add missing user_id, xp ---
def migrate_users():
    for uid, u in DATA["users"].items():
        u.setdefault("user_id", uid)
        u.setdefault("xp", 0)
        u.setdefault("streak", 0)
        u.setdefault("last_active", "")

# --- KEYBOARDS ---
def lang_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(LANGS["en"])], [KeyboardButton(LANGS["ru"])]],
        resize_keyboard=True
    )

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("➕ Add Task"), KeyboardButton("📋 List Tasks")],
            [KeyboardButton("✅ Mark Done"), KeyboardButton("📊 Daily Report")],
            [KeyboardButton("👤 Profile")]
        ], resize_keyboard=True
    )

# --- START ---
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    uid = str(message.from_user.id)
    if uid not in DATA["users"]:
        DATA["users"][uid] = {
            "user_id": uid, "lang": "en", "name": None, "tasks": [],
            "completed": 0, "xp": 0, "streak": 0, "last_active": ""
        }
        save_data()
    await message.answer(TEXTS["en"]["welcome"], reply_markup=lang_kb())

# --- LANGUAGE SELECTION ---
@dp.message(F.text.in_([v for v in LANGS.values()]))
async def choose_lang(message: Message):
    uid = str(message.from_user.id)
    lang = "en" if "English" in message.text else "ru"
    DATA["users"][uid]["lang"] = lang
    save_data()
    await message.answer(TEXTS[lang]["intro"], reply_markup=main_kb())

# --- HELP ---
@dp.message(F.text == "/help")
async def help_cmd(message: Message):
    lang = DATA["users"].get(str(message.from_user.id), {}).get("lang", "en")
    await message.answer(TEXTS[lang]["help"])

# --- ADD TASK ---
@dp.message(F.text == "➕ Add Task")
async def add_task_prompt(message: Message):
    await message.answer("✍️ Send me the task text to add.")

# --- LIST TASKS ---
@dp.message(F.text == "📋 List Tasks")
async def list_tasks(message: Message):
    uid = str(message.from_user.id)
    lang = DATA["users"][uid]["lang"]
    tasks = DATA["users"][uid]["tasks"]
    if not tasks:
        await message.answer(TEXTS[lang]["no_tasks"])
    else:
        await message.answer("\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]))

# --- MARK DONE ---
@dp.message(F.text == "✅ Mark Done")
async def mark_done_prompt(message: Message):
    uid = str(message.from_user.id)
    tasks = DATA["users"][uid]["tasks"]
    if not tasks:
        await message.answer(TEXTS[DATA["users"][uid]["lang"]]["no_tasks"])
        return
    await message.answer("Send the task number to mark as done:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]))

# --- PROFILE ---
@dp.message(F.text == "👤 Profile")
async def profile(message: Message):
    uid = str(message.from_user.id)
    u = DATA["users"][uid]
    lang = u["lang"]
    await message.answer(TEXTS[lang]["profile"].format(u["user_id"], u.get("name", "Not set"), u["completed"], u["streak"], u["xp"], rank(u["xp"])))

# --- DAILY REPORT ---
async def send_daily_report(uid):
    u = DATA["users"][uid]
    lang = u["lang"]
    total = len(u["tasks"])
    comp = u["completed"]
    percent = int((comp / (comp + total)) * 100) if comp + total else 0
    streak_msg = TEXTS[lang]["streak_ok"] if u["streak"] else TEXTS[lang]["streak_lost"]
    await bot.send_message(uid, TEXTS[lang]["report"].format(comp, total, percent, streak_msg, random.choice(MOTIVATIONS)))

@dp.message(F.text == "📊 Daily Report")
async def manual_report(message: Message):
    await send_daily_report(str(message.from_user.id))

# --- CATCH ALL (only add task text here) ---
@dp.message()
async def catch_all(message: Message):
    uid = str(message.from_user.id)
    text = message.text.strip()

    # Ignore commands
    if text.startswith("/"):
        return

    # Add as task
    DATA["users"][uid]["tasks"].append(text)
    save_data()
    lang = DATA["users"][uid]["lang"]
    await message.answer(TEXTS[lang]["task_added"].format(text))

# --- SCHEDULED REPORTS ---
async def scheduled_reports():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now == "21:00":
            for uid in DATA["users"]:
                await send_daily_report(uid)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# --- MAIN ---
async def main():
    load_data()
    migrate_users()
    print("✅ Bot running with language selection, streaks, reports, and motivations...")
    asyncio.create_task(scheduled_reports())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
