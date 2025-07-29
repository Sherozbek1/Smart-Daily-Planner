import asyncio
import json
import random
import os
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIG ---
BOT_TOKEN = "8387365932:AAGmMO0h2TVNE-bKpHME22sqWApfm7_UW6c"
ADMIN_ID = 5480597971

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

DATA_FILE = "data.json"
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)
DATA = {"users": {}}

# --- Load / Save ---
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
    # rotating backups
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(BACKUP_DIR, f"data_{timestamp}.json"), "w") as f:
        json.dump(DATA, f)
    files = sorted(os.listdir(BACKUP_DIR))
    if len(files) > 3:
        os.remove(os.path.join(BACKUP_DIR, files[0]))

# --- Languages & Texts ---
LANGUAGES = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}
TEXTS = {
    "en": {
        "welcome": "👋 Welcome to <b>Smart Daily Planner</b>!\nStay productive with tasks, streaks, XP, and more.\nChoose your language:",
        "instructions": "📚 <b>How to use:</b>\n• ➕ Add Task → add new task\n• ✅ Mark Done → complete task\n• 📊 Daily Report → stats at 21:00\n• 🏆 Leaderboard → top users\n• 👤 Profile → view XP, streaks, rank\n💡 Use /help anytime!",
        "help": "💡 <b>Help</b>:\n• Earn XP for tasks & streaks\n• Set deadlines (reminder 1h before)\n• Maintain streaks for bonuses\n• Ranks motivate you to grow!",
        "rank_info": "🎖 <b>Ranks</b>:\n🎯 Rookie Planner (0–199 XP)\n⚡ Focused Achiever (200–499 XP)\n🔥 Task Crusher (500–1199 XP)\n🏆 Consistency Master (1200–2499 XP)\n🌟 Productivity Legend (2500+ XP)",
        "no_tasks": "📭 You have no tasks.",
        "task_added": "🆕 Task added: {}\n⏳ Enter deadline in hours (1–24) or 0 for no deadline:",
        "deadline_set": "⏰ Deadline set at {}",
        "invalid_number": "❌ Invalid task number.",
        "task_done": "✅ Task completed: {}\n⭐ +3 XP",
        "profile": "👤 <b>Profile</b>\n🆔 ID: <code>{}</code>\n🏷️ Name: {}\n✅ Completed: {}\n🔥 Streak: {} days\n⭐ XP: {} ({})",
        "report": "📊 <b>Daily Report</b>\n✅ Completed: {}\n📌 Pending: {}\n🎯 Completion: {}%\n⭐ XP: {}\n\n💡 {}",
        "leaderboard": "🏆 <b>Leaderboard</b>\n{}",
        "tip": "💡 Tip: {}"
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в <b>Smart Daily Planner</b>!\nОставайтесь продуктивными с задачами, сериями и XP.\nВыберите язык:",
        "instructions": "📚 <b>Как использовать:</b>\n• ➕ Add Task → добавить задачу\n• ✅ Mark Done → выполнить задачу\n• 📊 Daily Report → отчет в 21:00\n• 🏆 Leaderboard → топ пользователей\n• 👤 Profile → XP, серии, ранг\n💡 Используйте /help в любое время!",
        "help": "💡 <b>Помощь</b>:\n• Получайте XP за задачи и серии\n• Устанавливайте дедлайны (напоминание за час)\n• Поддерживайте серии для бонусов\n• Ранги мотивируют расти!",
        "rank_info": "🎖 <b>Ранги</b>:\n🎯 Rookie Planner (0–199 XP)\n⚡ Focused Achiever (200–499 XP)\n🔥 Task Crusher (500–1199 XP)\n🏆 Consistency Master (1200–2499 XP)\n🌟 Productivity Legend (2500+ XP)",
        "no_tasks": "📭 У вас нет задач.",
        "task_added": "🆕 Задача добавлена: {}\n⏳ Введите дедлайн в часах (1–24) или 0, если без дедлайна:",
        "deadline_set": "⏰ Дедлайн установлен на {}",
        "invalid_number": "❌ Неверный номер задачи.",
        "task_done": "✅ Задача выполнена: {}\n⭐ +3 XP",
        "profile": "👤 <b>Профиль</b>\n🆔 ID: <code>{}</code>\n🏷️ Имя: {}\n✅ Выполнено: {}\n🔥 Серия: {} дней\n⭐ XP: {} ({})",
        "report": "📊 <b>Отчет</b>\n✅ Выполнено: {}\n📌 В ожидании: {}\n🎯 Завершено: {}%\n⭐ XP: {}\n\n💡 {}",
        "leaderboard": "🏆 <b>Таблица лидеров</b>\n{}",
        "tip": "💡 Совет: {}"
    }
}

MOTIVATIONS = {"en": ["🔥 Keep pushing!", "💪 Small steps daily!", "🚀 You’re improving!", "🌟 Stay consistent!", "🏆 Every task counts!"],
               "ru": ["🔥 Продолжай!", "💪 Маленькие шаги каждый день!", "🚀 Ты улучшаешься!", "🌟 Будь постоянен!", "🏆 Каждая задача важна!"]}
TIPS = {"en": ["Set deadlines to stay on track.", "Check profile to monitor streaks.", "Use reminders!", "Consistency = success!"],
        "ru": ["Устанавливайте дедлайны.", "Проверяйте профиль.", "Используйте напоминания!", "Постоянство = успех!"]}

# --- Keyboards ---
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton("➕ Add Task"), KeyboardButton("📋 List Tasks")],
        [KeyboardButton("✅ Mark Done"), KeyboardButton("📊 Daily Report")],
        [KeyboardButton("👤 Profile"), KeyboardButton("🏆 Leaderboard")]
    ], resize_keyboard=True)

# --- XP & Ranks ---
def rank(xp):
    if xp < 200: return "🎯 Rookie Planner"
    if xp < 500: return "⚡ Focused Achiever"
    if xp < 1200: return "🔥 Task Crusher"
    if xp < 2500: return "🏆 Consistency Master"
    return "🌟 Productivity Legend"

def add_xp(uid, amount):
    user = DATA["users"][uid]
    today = datetime.now().strftime("%Y-%m-%d")
    if user.get("xp_today_date") != today:
        user["xp_today"] = 0
        user["xp_today_date"] = today
    gain = min(amount, 15 - user["xp_today"])
    if gain > 0:
        user["xp"] += gain
        user["xp_today"] += gain

# --- Deadline & Streak ---
def update_streak(uid):
    user = DATA["users"][uid]
    today = datetime.now().strftime("%Y-%m-%d")
    last = user.get("last_active", "")
    if last == today: return
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    user["streak"] = user.get("streak", 0) + 1 if last == yesterday else 1
    bonus = 2 if user["streak"] < 4 else 5 if user["streak"] < 8 else 10
    user["xp"] += bonus
    user["last_active"] = today

def add_deadline(uid, task, hours):
    if hours > 0:
        deadline_time = (datetime.now() + timedelta(hours=hours)).timestamp()
        DATA["users"][uid].setdefault("deadlines", []).append({"task": task, "time": deadline_time, "reminded": False})

async def check_deadlines():
    while True:
        now = datetime.now().timestamp()
        for uid, u in DATA["users"].items():
            for d in u.get("deadlines", []):
                if not d["reminded"] and 0 < d["time"] - now < 3600:
                    await bot.send_message(uid, f"⏰ Reminder! Task <b>{d['task']}</b> is due in 1 hour!")
                    d["reminded"] = True
        await asyncio.sleep(600)

# --- START ---
@dp.message(F.text == "/start")
async def start(message: Message):
    uid = str(message.from_user.id)
    if uid not in DATA["users"]:
        DATA["users"][uid] = {"lang": "en", "name": None, "tasks": [], "deadlines": [],
                              "completed": 0, "streak": 0, "last_active": "",
                              "xp": 0, "xp_today": 0, "xp_today_date": ""}
        save_data()
    await message.answer(TEXTS["en"]["welcome"], reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(v, callback_data=f"lang:{k}")] for k, v in LANGUAGES.items()]))

# --- Callback: Set Language ---
@dp.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    lang = callback.data.split(":")[1]
    DATA["users"][uid]["lang"] = lang
    save_data()
    await callback.message.answer(TEXTS[lang]["instructions"])
    await callback.answer()

# --- Help ---
@dp.message(F.text == "/help")
async def help_cmd(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    await message.answer(TEXTS[lang]["help"])

# --- Ranks Info ---
@dp.message(F.text == "/ranks")
async def rank_cmd(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    await message.answer(TEXTS[lang]["rank_info"])

# --- Add Task ---
@dp.message(F.text == "➕ Add Task")
async def add_task(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    await message.answer("✍️ Send your task:" if lang == "en" else "✍️ Отправьте задачу:")

# --- Catch All ---
@dp.message()
async def catch_all(message: Message):
    uid = str(message.from_user.id)
    if message.text.startswith("/"): return
    lang = DATA["users"][uid]["lang"]
    text = message.text.strip()

    # Deadline input
    if "pending_task" in DATA["users"][uid] and text.isdigit():
        hours = int(text)
        task = DATA["users"][uid].pop("pending_task")
        add_deadline(uid, task, hours)
        await message.answer(TEXTS[lang]["deadline_set"].format(
            (datetime.now() + timedelta(hours=hours)).strftime("%H:%M")))
        save_data()
        return

    # Mark task done
    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(DATA["users"][uid]["tasks"]):
            task = DATA["users"][uid]["tasks"].pop(index)
            DATA["users"][uid]["completed"] += 1
            add_xp(uid, 3)
            update_streak(uid)
            save_data()
            await message.answer(TEXTS[lang]["task_done"].format(task))
        else:
            await message.answer(TEXTS[lang]["invalid_number"])
        return

    # Add new task
    DATA["users"][uid]["tasks"].append(text)
    DATA["users"][uid]["pending_task"] = text
    save_data()
    await message.answer(TEXTS[lang]["task_added"].format(text))

# --- Reports ---
async def send_report(uid):
    u = DATA["users"][uid]
    lang = u["lang"]
    tasks = len(u["tasks"]); comp = u["completed"]
    percent = int((comp/(comp+tasks))*100) if comp+tasks>0 else 0
    msg = TEXTS[lang]["report"].format(comp, tasks, percent, u["xp"], random.choice(MOTIVATIONS[lang]))
    await bot.send_message(uid, msg)

@dp.message(F.text == "📊 Daily Report")
async def manual_report(message: Message):
    await send_report(str(message.from_user.id))

# --- Profile ---
@dp.message(F.text == "👤 Profile")
async def profile(message: Message):
    uid = str(message.from_user.id); u = DATA["users"][uid]; lang = u["lang"]
    await message.answer(TEXTS[lang]["profile"].format(uid, u["name"], u["completed"], u["streak"], u["xp"], rank(u["xp"])))

# --- Leaderboard ---
@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    lb = sorted(DATA["users"].items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
    txt = "\n".join([f"{i+1}. {u['name']} – {u['xp']} XP ({rank(u['xp'])})" for i, (uid, u) in enumerate(lb)])
    await message.answer(TEXTS[lang]["leaderboard"].format(txt))

# --- Admin ---
@dp.message(F.text == "/stats")
async def stats(message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer(f"👥 Total users: {len(DATA['users'])}")

@dp.message(F.text == "/backup")
async def backup(message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer_document(open(DATA_FILE, "rb"))

# --- Scheduled Reports ---
async def scheduled_reports():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now in ["08:00", "14:00", "21:00"]:
            for uid in DATA["users"]:
                await send_report(uid)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# --- MAIN ---
async def main():
    load_data()
    asyncio.create_task(scheduled_reports())
    asyncio.create_task(check_deadlines())
    print("✅ Bot running with deadlines, streaks, XP, multilingual support")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
