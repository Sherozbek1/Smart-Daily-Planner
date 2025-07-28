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
BOT_TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# --- FILE STORAGE ---
DATA_FILE = "data.json"
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
def get_streak_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Enable", callback_data="streak:yes")],
        [InlineKeyboardButton(text="❌ Disable", callback_data="streak:no")]
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
            "tasks": [],
            "completed": 0,
            "streak": 0,
            "last_active": "",
            "name": None,
            "streak_enabled": False
        }
        save_data()
    await message.answer(
        "👋 Welcome to <b>Smart Daily Planner</b>!\n\n"
        "I’ll help you stay productive and track your progress.\n"
        "First, tell me your nickname (2–20 characters)."
    )

# --- NICKNAME SETUP ---
@dp.message(F.text.regexp("^[A-Za-z0-9_]{2,20}$"))
async def set_nickname(message: Message):
    uid = str(message.from_user.id)
    if DATA["users"][uid].get("name") is None:
        DATA["users"][uid]["name"] = message.text
        save_data()
        await message.answer(
            f"✅ Nice to meet you, <b>{message.text}</b>!\n"
            "Do you want to enable 🔥 <b>Streak Mode</b>?\n"
            "Streak increases only if you complete ≥80% of tasks daily.",
            reply_markup=get_streak_markup()
        )
    else:
        await catch_all(message)

@dp.callback_query(F.data.startswith("streak:"))
async def set_streak_mode(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    choice = callback.data.split(":")[1]
    DATA["users"][uid]["streak_enabled"] = (choice == "yes")
    save_data()
    status = "enabled ✅" if choice == "yes" else "disabled ❌"
    await callback.message.answer(
        f"🔥 Streak mode {status}.\nYou can now start adding tasks!",
        reply_markup=get_main_reply_keyboard()
    )
    await callback.answer()

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
    streak_info = f"🔥 Streak: {user['streak']} days" if user.get("streak_enabled") else "🔥 Streak Mode: Disabled"
    await message.answer(
        f"👤 <b>Profile</b>\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"🏷️ Name: {user.get('name', 'Not set')}\n"
        f"✅ Tasks Completed: {user['completed']}\n"
        f"{streak_info}"
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
            tasks.pop(index)
            DATA["users"][uid]["completed"] += 1
            save_data()
            await message.answer("✅ Task marked as done!")
        else:
            await message.answer("❌ Invalid task number.")
    else:
        DATA["users"][uid]["tasks"].append(text)
        save_data()
        await message.answer(f"🆕 Task added: {text}")

# --- SEND DAILY REPORT ---
async def send_daily_report(uid):
    user = DATA["users"][uid]
    tasks = user["tasks"]
    total = len(tasks)
    completed = user["completed"]
    percent = int((completed / (completed + total)) * 100) if (completed + total) else 0
    motivation = random.choice(MOTIVATIONS)

    if user.get("streak_enabled") and percent >= 80:
        user["streak"] += 1
    save_data()

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
            for uid in list(DATA["users"].keys()):
                await send_daily_report(uid)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# --- MAIN ---
async def main():
    load_data()
    print("✅ Bot is running with Streak Mode and 9 PM reports...")
    asyncio.create_task(scheduled_reports())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
