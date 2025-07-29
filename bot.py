import asyncio
import json
import random
import os
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# === CONFIG ===
BOT_TOKEN = "8387365932:AAGmMO0h2TVNE-bKpHME22sqWApfm7_UW6c"
ADMIN_ID = 5480597971

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

DATA_FILE = "data.json"
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)
DATA = {"users": {}}

# === Languages ===
LANGUAGES = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}
TEXTS = {
    "en": {
        "welcome": "👋 Welcome to <b>Smart Daily Planner</b>!\nStay productive with tasks, streaks, XP, and more.\nChoose your language:",
        "instructions": "📚 <b>How to use:</b>\n• ➕ Add Task → add new task\n• ✅ Mark Done → complete task\n• 📊 Daily Report → stats at 21:00\n• 🏆 Leaderboard → top users\n• 👤 Profile → view XP, streaks, rank\n💡 Use /help anytime!",
        "help": "💡 Use buttons to manage tasks, track progress and stay motivated!",
        "rank_info": "🎖 Ranks:\n🎯 Rookie Planner (0–199 XP)\n⚡ Focused Achiever (200–499 XP)\n🔥 Task Crusher (500–1199 XP)\n🏆 Consistency Master (1200–2499 XP)\n🌟 Productivity Legend (2500+ XP)",
        "no_tasks": "📭 You have no tasks.",
        "task_added": "🆕 Task added: {}",
        "task_done": "✅ Task completed: {}\n⭐ +3 XP",
        "invalid_number": "❌ Invalid task number.",
        "profile": "👤 <b>Profile</b>\nName: {}\n✅ Completed: {}\n🔥 Streak: {} days\n⭐ XP: {} ({})",
        "leaderboard": "🏆 <b>Leaderboard</b>\n{}",
        "report": "📊 <b>Daily Report</b>\n✅ Completed: {}\n📌 Pending: {}\n🎯 Completion: {}%\n⭐ XP: {}\n\n💡 {}",
        "tip": "💡 Tip: {}",
        "choose_task_num": "Reply with the task number to mark as done:"
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в <b>Smart Daily Planner</b>!\nОставайтесь продуктивными с задачами, сериями и XP.\nВыберите язык:",
        "instructions": "📚 <b>Как использовать:</b>\n• ➕ Add Task → добавить задачу\n• ✅ Mark Done → выполнить задачу\n• 📊 Daily Report → отчет в 21:00\n• 🏆 Leaderboard → топ пользователей\n• 👤 Profile → XP, серии, ранг\n💡 Используйте /help в любое время!",
        "help": "💡 Используйте кнопки для управления задачами, отслеживания прогресса и мотивации!",
        "rank_info": "🎖 Ранги:\n🎯 Rookie Planner (0–199 XP)\n⚡ Focused Achiever (200–499 XP)\n🔥 Task Crusher (500–1199 XP)\n🏆 Consistency Master (1200–2499 XP)\n🌟 Productivity Legend (2500+ XP)",
        "no_tasks": "📭 У вас нет задач.",
        "task_added": "🆕 Задача добавлена: {}",
        "task_done": "✅ Задача выполнена: {}\n⭐ +3 XP",
        "invalid_number": "❌ Неверный номер задачи.",
        "profile": "👤 <b>Профиль</b>\nИмя: {}\n✅ Выполнено: {}\n🔥 Серия: {} дней\n⭐ XP: {} ({})",
        "leaderboard": "🏆 <b>Таблица лидеров</b>\n{}",
        "report": "📊 <b>Отчет</b>\n✅ Выполнено: {}\n📌 В ожидании: {}\n🎯 Завершено: {}%\n⭐ XP: {}\n\n💡 {}",
        "tip": "💡 Совет: {}",
        "choose_task_num": "Напишите номер задачи, чтобы отметить её выполненной:"
    }
}
MOTIVATIONS = {
    "en": ["🔥 Keep pushing!", "💪 Small steps daily!", "🚀 You’re improving!", "🌟 Stay consistent!"],
    "ru": ["🔥 Продолжай!", "💪 Маленькие шаги каждый день!", "🚀 Ты улучшаешься!", "🌟 Будь постоянен!"]
}
TIPS = {
    "en": ["Set deadlines to stay on track.", "Check profile to monitor streaks.", "Use reminders!", "Consistency = success!"],
    "ru": ["Устанавливайте дедлайны.", "Проверяйте профиль.", "Используйте напоминания!", "Постоянство = успех!"]
}

# === Storage ===
def load_data():
    global DATA
    try:
        with open(DATA_FILE, "r") as f: DATA = json.load(f)
    except FileNotFoundError: DATA = {"users": {}}

def save_data():
    with open(DATA_FILE, "w") as f: json.dump(DATA, f)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(BACKUP_DIR, f"data_{ts}.json"), "w") as f: json.dump(DATA, f)
    files = sorted(os.listdir(BACKUP_DIR))
    if len(files) > 5: os.remove(os.path.join(BACKUP_DIR, files[0]))

# === Utils ===
def user_lang(uid): return DATA["users"][uid].get("lang", "en")
def rank(xp):
    return "🎯 Rookie Planner" if xp < 200 else \
           "⚡ Focused Achiever" if xp < 500 else \
           "🔥 Task Crusher" if xp < 1200 else \
           "🏆 Consistency Master" if xp < 2500 else "🌟 Productivity Legend"

def add_xp(uid, amount): DATA["users"][uid]["xp"] += amount
def update_streak(uid):
    u = DATA["users"][uid]
    today = datetime.now().strftime("%Y-%m-%d")
    if u.get("last_active") != today:
        yest = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        u["streak"] = u.get("streak", 0) + 1 if u.get("last_active") == yest else 1
        u["last_active"] = today

# === Keyboards ===
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("➕ Add Task"), KeyboardButton("📋 List Tasks")],
            [KeyboardButton("✅ Mark Done"), KeyboardButton("📊 Daily Report")],
            [KeyboardButton("👤 Profile"), KeyboardButton("🏆 Leaderboard")]
        ], resize_keyboard=True
    )

# === Handlers ===
@dp.message(F.text == "/start")
async def start_cmd(m: Message):
    uid = str(m.from_user.id)
    if uid not in DATA["users"]:
        DATA["users"][uid] = {"name": m.from_user.first_name, "lang": "en",
                              "tasks": [], "completed": 0, "xp": 0,
                              "streak": 0, "last_active": "", "adding": False, "marking": False}
        save_data()
    await m.answer(TEXTS["en"]["welcome"], reply_markup=main_kb())

@dp.message(F.text == "➕ Add Task")
async def ask_task(m: Message):
    uid = str(m.from_user.id); lang = user_lang(uid)
    DATA["users"][uid]["adding"] = True; save_data()
    await m.answer("✍️ Send your task:" if lang == "en" else "✍️ Отправьте задачу:")

@dp.message(F.text == "📋 List Tasks")
async def list_tasks(m: Message):
    uid = str(m.from_user.id); lang = user_lang(uid); u = DATA["users"][uid]
    if not u["tasks"]:
        await m.answer(TEXTS[lang]["no_tasks"])
    else:
        msg = "\n".join([f"{i+1}. {t}" for i, t in enumerate(u["tasks"])])
        await m.answer("📋 Tasks:\n" + msg)

@dp.message(F.text == "✅ Mark Done")
async def ask_done(m: Message):
    uid = str(m.from_user.id); lang = user_lang(uid)
    u = DATA["users"][uid]
    if not u["tasks"]: await m.answer(TEXTS[lang]["no_tasks"]); return
    DATA["users"][uid]["marking"] = True; save_data()
    await m.answer(TEXTS[lang]["choose_task_num"])

@dp.message(F.text == "👤 Profile")
async def profile(m: Message):
    uid = str(m.from_user.id); u = DATA["users"][uid]; lang = user_lang(uid)
    await m.answer(TEXTS[lang]["profile"].format(u["name"], u["completed"], u["streak"], u["xp"], rank(u["xp"])))

@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(m: Message):
    uid = str(m.from_user.id); lang = user_lang(uid)
    lb = sorted(DATA["users"].values(), key=lambda x: x.get("xp", 0), reverse=True)[:10]
    text = "\n".join([f"{i+1}. {u['name']} – {u['xp']} XP" for i, u in enumerate(lb)])
    await m.answer(TEXTS[lang]["leaderboard"].format(text))

@dp.message(F.text == "📊 Daily Report")
async def daily_report(m: Message): await send_report(str(m.from_user.id))

@dp.message()
async def handle_input(m: Message):
    uid = str(m.from_user.id)
    if uid not in DATA["users"]: return
    lang = user_lang(uid); u = DATA["users"][uid]

    if u.get("adding"):
        u["tasks"].append(m.text); u["adding"] = False; save_data()
        await m.answer(TEXTS[lang]["task_added"].format(m.text)); return

    if u.get("marking") and m.text.isdigit():
        idx = int(m.text)-1
        if 0 <= idx < len(u["tasks"]):
            task = u["tasks"].pop(idx); u["completed"] += 1
            add_xp(uid, 3); update_streak(uid); u["marking"] = False; save_data()
            await m.answer(TEXTS[lang]["task_done"].format(task))
        else: await m.answer(TEXTS[lang]["invalid_number"])
        return

# === Reports & Deadlines ===
async def send_report(uid):
    u = DATA["users"][uid]; lang = u["lang"]
    tasks = len(u["tasks"]); comp = u["completed"]
    percent = int((comp/(comp+tasks))*100) if (comp+tasks)>0 else 0
    tip = random.choice(TIPS[lang]); mot = random.choice(MOTIVATIONS[lang])
    msg = TEXTS[lang]["report"].format(comp, tasks, percent, u["xp"], f"{mot} | {tip}")
    await bot.send_message(uid, msg)

async def scheduled_reports():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now in ["08:00", "14:00", "21:00"]:
            for uid in DATA["users"]: await send_report(uid)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# === Admin Commands ===
@dp.message(F.text == "/stats")
async def stats_cmd(m: Message):
    if m.from_user.id == ADMIN_ID: await m.answer(f"👥 Users: {len(DATA['users'])}")

@dp.message(F.text == "/backup")
async def backup_cmd(m: Message):
    if m.from_user.id == ADMIN_ID:
        await m.answer_document(open(DATA_FILE, "rb"))

# === Main Loop ===
async def main():
    load_data()
    asyncio.create_task(scheduled_reports())
    print("✅ Bot Running with full features")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
