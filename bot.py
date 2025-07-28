import asyncio
import json
import random
from datetime import datetime, timedelta
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

# --- LANGUAGES ---
LANGUAGES = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}

# --- DATA STORAGE ---
USER_LANGS = {}
USER_TASKS = {}
USER_STATS = {}  # {user_id: {"completed": int, "streak": int, "last_active": "YYYY-MM-DD"}}

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

# --- INLINE LANGUAGE SELECTION ---
def get_language_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANGUAGES[code], callback_data=f"lang:{code}")]
        for code in LANGUAGES
    ])

# --- MAIN KEYBOARD ---
def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Add Task"), KeyboardButton(text="📋 List Tasks")],
        [KeyboardButton(text="✅ Mark Done"), KeyboardButton(text="📊 Daily Report")],
        [KeyboardButton(text="👤 Profile")]
    ], resize_keyboard=True)

# --- START COMMAND ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Please choose your language:", reply_markup=get_language_markup())

@dp.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery):
    lang_code = callback.data.split(":")[1]
    USER_LANGS[callback.from_user.id] = lang_code
    await callback.message.answer(
        f"Language set to {LANGUAGES[lang_code]}.\n\nWhat would you like to do?",
        reply_markup=get_main_reply_keyboard()
    )
    await callback.answer()

# --- ADD TASK ---
@dp.message(F.text == "➕ Add Task")
async def add_task(message: Message):
    await message.answer("Send me the task you want to add.")

# --- LIST TASKS ---
@dp.message(F.text == "📋 List Tasks")
async def list_tasks(message: Message):
    uid = message.from_user.id
    tasks = USER_TASKS.get(uid, [])
    if not tasks:
        await message.answer("You have no tasks.")
    else:
        await message.answer("Here are your tasks:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]))

# --- MARK DONE ---
@dp.message(F.text == "✅ Mark Done")
async def done_task_prompt(message: Message):
    uid = message.from_user.id
    tasks = USER_TASKS.get(uid, [])
    if not tasks:
        await message.answer("You have no tasks.")
        return
    await message.answer("Send the number of the task to mark as done:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]))

# --- DAILY REPORT (User Requested) ---
@dp.message(F.text == "📊 Daily Report")
async def daily_report(message: Message):
    await send_daily_report(message.from_user.id)

# --- PROFILE SECTION ---
@dp.message(F.text == "👤 Profile")
async def profile(message: Message):
    uid = message.from_user.id
    stats = USER_STATS.get(uid, {"completed": 0, "streak": 0})
    await message.answer(
        f"👤 <b>Your Profile</b>\n"
        f"✅ Tasks Completed: {stats['completed']}\n"
        f"🔥 Streak: {stats['streak']} days"
    )

# --- CATCH-ALL: Task Adding & Marking Done ---
@dp.message()
async def catch_all(message: Message):
    uid = message.from_user.id
    text = message.text.strip()

    # ✅ Ignore all commands so they don't become tasks
    if text.startswith("/"):
        return

    if text.isdigit():  # marking task as done
        index = int(text) - 1
        tasks = USER_TASKS.get(uid, [])
        if 0 <= index < len(tasks):
            task = tasks.pop(index)
            update_user_stats(uid)
            await message.answer(f"✅ Task marked as done: {task}")
        else:
            await message.answer("Invalid task number.")
    else:  # adding task
        USER_TASKS.setdefault(uid, []).append(text)
        await message.answer(f"Task added: {text}")

# --- HELPER: Update Streak & Stats ---
def update_user_stats(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    stats = USER_STATS.setdefault(uid, {"completed": 0, "streak": 0, "last_active": ""})

    stats["completed"] += 1
    if stats["last_active"] == today:
        return
    if stats["last_active"] == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
        stats["streak"] += 1
    else:
        stats["streak"] = 1
    stats["last_active"] = today

# --- HELPER: Send Daily Report ---
async def send_daily_report(uid):
    tasks = USER_TASKS.get(uid, [])
    total = len(tasks)
    completed = USER_STATS.get(uid, {}).get("completed", 0)
    percent = int((completed / (completed + total)) * 100) if (completed + total) else 0
    motivation = random.choice(MOTIVATIONS)

    await bot.send_message(uid,
        f"📊 <b>Daily Report</b>\n"
        f"✅ Completed: {completed}\n"
        f"📌 Pending: {total}\n"
        f"🎯 Completion: {percent}%\n\n"
        f"💡 {motivation}"
    )

# --- CRON JOB ENDPOINT (For External Trigger) ---
@dp.message(F.text == "/send_report_all")
async def send_report_all(message: Message):
    print("🔥 /send_report_all triggered!")
    all_users = {5480597971} | set(USER_TASKS.keys())
    
    for uid in all_users:
        try:
            print(f"➡️ Sending report to {uid}")
            await send_daily_report(uid)
        except Exception as e:
            print(f"❌ Failed to send to {uid}: {e}")
    
    await message.answer("✅ Reports attempted for all users (check logs).")



# ✅ Test command to send report to you manually
@dp.message(F.text == "/send_me_report")
async def send_me_report(message: Message):
    await send_daily_report(5480597971)
    await message.answer("📨 Sent report to you manually!")

# --- MAIN ---
async def main():
    print("✅ Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
