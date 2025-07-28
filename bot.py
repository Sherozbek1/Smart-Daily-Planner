import asyncio
import json
import random
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# --- BOT TOKEN ---
BOT_TOKEN = "8387365932:AAGmMO0h2TVNE-bKpHME22sqWApfm7_UW6c"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# --- FILE STORAGE ---
DATA_FILE = "data.json"

# --- DATA STRUCTURES ---
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

# --- LANGUAGES ---
LANGUAGES = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}

# --- MOTIVATIONAL MESSAGES ---
MOTIVATIONS = [
    "🔥 Keep pushing, you’re doing amazing!",
    "💪 Small steps every day lead to big success.",
    "🚀 You’re on your way to greatness, keep going!",
    "🌟 Consistency beats motivation. Stay consistent!",
    "🏆 Every completed task is a victory. Well done!",
    "🌱 Grow a little every day, success will follow.",
    "⚡ Your effort today builds your future tomorrow."
]

# --- KEYBOARDS ---
def get_language_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANGUAGES[code], callback_data=f"lang:{code}")]
        for code in LANGUAGES
    ])

def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Add Task"), KeyboardButton(text="📋 List Tasks")],
        [KeyboardButton(text="✅ Mark Done"), KeyboardButton(text="📊 Daily Report")],
        [KeyboardButton(text="👤 Profile")]
    ], resize_keyboard=True)

# --- START COMMAND ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    uid = str(message.from_user.id)
    if uid not in DATA["users"]:
        DATA["users"][uid] = {
            "lang": "en",
            "tasks": [],
            "completed": 0,
            "streak": 0,
            "last_active": "",
            "name": None
        }
        save_data()
    await message.answer(
        "👋 Welcome to <b>Smart Daily Planner</b>!\n\n"
        "I'll help you stay productive and track your progress.\n"
        "First, choose your language:", reply_markup=get_language_markup()
    )

@dp.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    lang_code = callback.data.split(":")[1]
    DATA["users"][uid]["lang"] = lang_code
    save_data()
    await callback.message.answer(
        f"✅ Language set to {LANGUAGES[lang_code]}.\n\nWhat's your nickname? (Type it below)",
    )
    await callback.answer()

# --- NICKNAME SETUP ---
@dp.message(F.text.regexp("^[A-Za-z0-9_]{2,20}$"))
async def set_nickname(message: Message):
    uid = str(message.from_user.id)
    if DATA["users"][uid].get("name") is None:
        DATA["users"][uid]["name"] = message.text
        save_data()
        await message.answer(
            f"✅ Nice to meet you, <b>{message.text}</b>!\n"
            "Now you can start adding tasks or check your profile.",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        await catch_all(message)

# --- ADD TASK ---
@dp.message(F.text == "➕ Add Task")
async def add_task(message: Message):
    await message.answer("✍️ Send me the task you want to add.")

# --- LIST TASKS ---
@dp.message(F.text == "📋 List Tasks")
async def list_tasks(message: Message):
    uid = str(message.from_user.id)
    tasks = DATA["users"][uid]["tasks"]
    if not tasks:
        await message.answer("📭 You have no tasks.")
    else:
        await message.answer("📝 Your tasks:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]))

# --- MARK DONE ---
@dp.message(F.text == "✅ Mark Done")
async def done_task_prompt(message: Message):
    uid = str(message.from_user.id)
    tasks = DATA["users"][uid]["tasks"]
    if not tasks:
        await message.answer("📭 You have no tasks.")
        return
    await message.answer("Send the number of the task to mark as done:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]))

# --- DAILY REPORT ---
@dp.message(F.text == "📊 Daily Report")
async def daily_report(message: Message):
    await send_daily_report(str(message.from_user.id))

# --- PROFILE ---
@dp.message(F.text == "👤 Profile")
async def profile(message: Message):
    uid = str(message.from_user.id)
    user = DATA["users"][uid]
    await message.answer(
        f"👤 <b>Profile</b>\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"🏷️ Name: {user.get('name', 'Not set')}\n"
        f"✅ Tasks Completed: {user['completed']}\n"
        f"🔥 Streak: {user['streak']} days"
    )

# --- CATCH-ALL ---
@dp.message()
async def catch_all(message: Message):
    uid = str(message.from_user.id)
    text = message.text.strip()

    if text.isdigit():  
        index = int(text) - 1
        tasks = DATA["users"][uid]["tasks"]
        if 0 <= index < len(tasks):
            task = tasks.pop(index)
            update_user_stats(uid)
            save_data()
            await message.answer(f"✅ Task marked as done: {task}")
        else:
            await message.answer("❌ Invalid task number.")
    else:
        DATA["users"][uid]["tasks"].append(text)
        save_data()
        await message.answer(f"🆕 Task added: {text}")

# --- UPDATE STATS ---
def update_user_stats(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    user = DATA["users"][uid]
    user["completed"] += 1
    if user["last_active"] == today:
        return
    if user["last_active"] == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
        user["streak"] += 1
    else:
        user["streak"] = 1
    user["last_active"] = today

# --- SEND DAILY REPORT ---
async def send_daily_report(uid):
    user = DATA["users"][uid]
    tasks = user["tasks"]
    total = len(tasks)
    completed = user["completed"]
    percent = int((completed / (completed + total)) * 100) if (completed + total) else 0
    motivation = random.choice(MOTIVATIONS)

    await bot.send_message(uid,
        f"📊 <b>Daily Report</b>\n"
        f"✅ Completed: {completed}\n"
        f"📌 Pending: {total}\n"
        f"🎯 Completion: {percent}%\n\n"
        f"💡 {motivation}"
    )

# --- SCHEDULED REPORTS AT 9 PM UZ TIME ---
async def scheduled_reports():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now == "21:00":
            print("⏰ Sending scheduled reports...")
            for uid in DATA["users"].keys():
                await send_daily_report(uid)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# --- MAIN ---
async def main():
    load_data()
    print("✅ Bot is running with 9 PM Uzbekistan reports...")
    asyncio.create_task(scheduled_reports())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
