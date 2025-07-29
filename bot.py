import asyncio
import json
import random
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIG ---
BOT_TOKEN = "8387365932:AAGmMO0h2TVNE-bKpHME22sqWApfm7_UW6c"
ADMIN_ID = 5480597971   # replace with your Telegram ID

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

DATA_FILE = "data.json"
BACKUP_FILE = "data_backup.json"
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
    with open(BACKUP_FILE, "w") as f:
        json.dump(DATA, f)

# --- Languages ---
LANGUAGES = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}

TEXTS = {
    "en": {
        "welcome": "👋 Welcome to <b>Smart Daily Planner</b>!\nI'll help you stay productive.\nChoose your language:",
        "ask_name": "🏷️ What's your nickname? (2–20 letters)",
        "name_set": "✅ Nice to meet you, <b>{}</b>! Start adding tasks or view your profile.",
        "no_tasks": "📭 You have no tasks.",
        "task_added": "🆕 Task added: {}",
        "invalid_number": "❌ Invalid task number.",
        "task_done": "✅ Task marked as done: {}",
        "profile": "👤 <b>Profile</b>\n🆔 ID: <code>{}</code>\n🏷️ Name: {}\n✅ Completed: {}\n🔥 Streak: {} days\n⭐ XP: {} ({})",
        "report": "📊 <b>Daily Report</b>\n✅ Completed: {}\n📌 Pending: {}\n🎯 Completion: {}%\n⭐ XP: {}\n\n💡 {}",
        "tip": "💡 Tip: {}",
        "leaderboard": "🏆 <b>Leaderboard</b>\n{}"
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в <b>Smart Daily Planner</b>!\nЯ помогу вам быть продуктивным.\nВыберите язык:",
        "ask_name": "🏷️ Какой у вас ник? (2–20 букв)",
        "name_set": "✅ Рад знакомству, <b>{}</b>! Начните добавлять задачи или посмотрите профиль.",
        "no_tasks": "📭 У вас нет задач.",
        "task_added": "🆕 Задача добавлена: {}",
        "invalid_number": "❌ Неверный номер задачи.",
        "task_done": "✅ Задача выполнена: {}",
        "profile": "👤 <b>Профиль</b>\n🆔 ID: <code>{}</code>\n🏷️ Имя: {}\n✅ Выполнено: {}\n🔥 Серия: {} дней\n⭐ XP: {} ({})",
        "report": "📊 <b>Ежедневный отчет</b>\n✅ Выполнено: {}\n📌 В ожидании: {}\n🎯 Завершено: {}%\n⭐ XP: {}\n\n💡 {}",
        "tip": "💡 Совет: {}",
        "leaderboard": "🏆 <b>Таблица лидеров</b>\n{}"
    }
}

MOTIVATIONS = {
    "en": [
        "🔥 Keep pushing, you’re doing amazing!",
        "💪 Small steps every day lead to big success.",
        "🚀 You’re on your way to greatness, keep going!",
        "🌟 Consistency beats motivation. Stay consistent!",
        "🏆 Every completed task is a victory. Well done!"
    ],
    "ru": [
        "🔥 Продолжай, ты отлично справляешься!",
        "💪 Маленькие шаги каждый день приводят к успеху.",
        "🚀 Ты на пути к величию, не сдавайся!",
        "🌟 Постоянство важнее мотивации. Будь постоянен!",
        "🏆 Каждая выполненная задача — это победа!"
    ]
}

TIPS = {
    "en": [
        "Set deadlines to stay on track.",
        "Check your profile to monitor streaks!",
        "Use reminders to never miss a task.",
        "Consistency is key — complete at least 80% daily!"
    ],
    "ru": [
        "Устанавливайте дедлайны, чтобы быть в форме.",
        "Проверяйте профиль, чтобы следить за серией!",
        "Используйте напоминания, чтобы ничего не забыть.",
        "Постоянство — ключ! Выполняйте минимум 80% задач."
    ]
}

# --- Keyboards ---
def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Add Task"), KeyboardButton(text="📋 List Tasks")],
        [KeyboardButton(text="✅ Mark Done"), KeyboardButton(text="📊 Daily Report")],
        [KeyboardButton(text="👤 Profile"), KeyboardButton(text="🏆 Leaderboard")]
    ], resize_keyboard=True)

# --- XP / Ranks ---
def get_rank(xp):
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

# --- Start ---
@dp.message(F.text == "/start")
async def start(message: Message):
    uid = str(message.from_user.id)
    if uid not in DATA["users"]:
        DATA["users"][uid] = {
            "lang": "en", "name": None, "tasks": [], "completed": 0, "streak": 0, "last_active": "",
            "xp": 0, "xp_today": 0, "xp_today_date": ""
        }
        save_data()
    await message.answer(TEXTS["en"]["welcome"], reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=v, callback_data=f"lang:{k}")] for k, v in LANGUAGES.items()]
    ))

@dp.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    lang = callback.data.split(":")[1]
    DATA["users"][uid]["lang"] = lang
    save_data()
    await callback.message.answer(TEXTS[lang]["ask_name"])
    await callback.answer()

@dp.message(F.text.regexp("^[A-Za-zА-Яа-я0-9_]{2,20}$"))
async def set_name(message: Message):
    uid = str(message.from_user.id)
    lang = DATA["users"][uid]["lang"]
    if DATA["users"][uid]["name"] is None:
        DATA["users"][uid]["name"] = message.text
        save_data()
        await message.answer(TEXTS[lang]["name_set"].format(message.text), reply_markup=get_main_reply_keyboard())
    else:
        await catch_all(message)

# --- Add Task ---
@dp.message(F.text == "➕ Add Task")
async def add_task(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    await message.answer("✍️ Send me the task to add:" if lang=="en" else "✍️ Отправьте задачу для добавления:")

# --- List Tasks ---
@dp.message(F.text == "📋 List Tasks")
async def list_tasks(message: Message):
    uid = str(message.from_user.id)
    lang = DATA["users"][uid]["lang"]
    tasks = DATA["users"][uid]["tasks"]
    if not tasks:
        await message.answer(TEXTS[lang]["no_tasks"])
    else:
        await message.answer("\n".join([f"{i+1}. {t}" for i,t in enumerate(tasks)]))

# --- Mark Done ---
@dp.message(F.text == "✅ Mark Done")
async def done_task_prompt(message: Message):
    uid = str(message.from_user.id)
    lang = DATA["users"][uid]["lang"]
    tasks = DATA["users"][uid]["tasks"]
    if not tasks:
        await message.answer(TEXTS[lang]["no_tasks"])
        return
    await message.answer("\n".join([f"{i+1}. {t}" for i,t in enumerate(tasks)]))

# --- Daily Report ---
@dp.message(F.text == "📊 Daily Report")
async def manual_report(message: Message):
    await send_daily_report(str(message.from_user.id))

# --- Profile ---
@dp.message(F.text == "👤 Profile")
async def profile(message: Message):
    uid = str(message.from_user.id)
    u = DATA["users"][uid]
    lang = u["lang"]
    await message.answer(TEXTS[lang]["profile"].format(uid, u["name"], u["completed"], u["streak"], u["xp"], get_rank(u["xp"])))

# --- Leaderboard ---
@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: Message):
    lang = DATA["users"][str(message.from_user.id)]["lang"]
    lb = sorted(DATA["users"].items(), key=lambda x: x[1].get("xp",0), reverse=True)[:10]
    txt = "\n".join([f"{i+1}. {u['name']} – {u['xp']} XP ({get_rank(u['xp'])})" for i,(uid,u) in enumerate(lb)])
    await message.answer(TEXTS[lang]["leaderboard"].format(txt))

# --- Catch-All (Add/Complete Tasks) ---
@dp.message()
async def catch_all(message: Message):
    uid = str(message.from_user.id)
    lang = DATA["users"][uid]["lang"]
    text = message.text.strip()

    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(DATA["users"][uid]["tasks"]):
            task = DATA["users"][uid]["tasks"].pop(index)
            DATA["users"][uid]["completed"] += 1
            add_xp(uid, 3)
            save_data()
            await message.answer(TEXTS[lang]["task_done"].format(task))
        else:
            await message.answer(TEXTS[lang]["invalid_number"])
    else:
        DATA["users"][uid]["tasks"].append(text)
        save_data()
        await message.answer(TEXTS[lang]["task_added"].format(text))

# --- Send Report ---
async def send_daily_report(uid):
    u = DATA["users"][uid]
    lang = u["lang"]
    tasks = len(u["tasks"])
    comp = u["completed"]
    percent = int((comp/(comp+tasks))*100) if comp+tasks>0 else 0
    msg = TEXTS[lang]["report"].format(comp, tasks, percent, u["xp"], random.choice(MOTIVATIONS[lang]))
    await bot.send_message(uid, msg)

# --- Scheduled Reminders ---
async def scheduled_reports():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now in ["08:00","14:00","21:00"]:
            for uid in DATA["users"]:
                await send_daily_report(uid)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# --- Admin Commands ---
@dp.message(F.text.startswith("/stats"))
async def stats(message: Message):
    if message.from_user.id != ADMIN_ID: return
    total = len(DATA["users"])
    await message.answer(f"👥 Total users: {total}")

@dp.message(F.text.startswith("/backup"))
async def backup(message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer_document(open(DATA_FILE,"rb"))

# --- Main ---
async def main():
    load_data()
    asyncio.create_task(scheduled_reports())
    print("✅ Bot running with XP, Leaderboard, Bilingual & Tips")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
