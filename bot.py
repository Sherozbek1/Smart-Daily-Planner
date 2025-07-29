import json
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F
import asyncio
import os

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789  # Replace with your Telegram ID

data_file = "user_data.json"

def load_data():
    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

def get_tip():
    tips = [
        "🧠 Tip: Break your work into 25-minute chunks (Pomodoro).",
        "💧 Tip: Stay hydrated for better focus!",
        "📵 Tip: Put your phone on Do Not Disturb when working.",
        "📋 Tip: Prioritize your top 3 tasks today.",
        "⏰ Tip: Review your tasks every night for the next day."
    ]
    return random.choice(tips)

def get_main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add Task", callback_data="add_task")
    kb.button(text="📋 My Tasks", callback_data="view_tasks")
    kb.button(text="✅ Done Task", callback_data="mark_done")
    kb.button(text="🔥 Tip", callback_data="show_tip")
    return kb.as_markup()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

@dp.message(F.text == "/start")
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in data:
        data[user_id] = {"tasks": [], "xp": 0, "streak": 0, "last_done": ""}
        save_data(data)
    desc = """
👋 <b>Welcome to your Productivity Buddy!</b>

Track tasks ✅
Earn XP 🌟
Maintain streaks 🔥
Stay motivated 💪

Click a button below to begin 👇
"""
    await message.answer(desc, reply_markup=get_main_keyboard())

@dp.message(F.text == "/help")
async def help_command(message: types.Message):
    await message.answer("Use the buttons to manage tasks. Commands: /start /help /tip")

@dp.message(F.text == "/tip")
async def tip_command(message: types.Message):
    await message.answer(get_tip())

@dp.callback_query(F.data == "add_task")
async def ask_task(callback: types.CallbackQuery):
    await callback.message.answer("📝 Send the task you want to add:")

@dp.message()
async def capture_task(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text
    if user_id not in data:
        data[user_id] = {"tasks": [], "xp": 0, "streak": 0, "last_done": ""}

    if "awaiting_task" in data[user_id]:
        data[user_id]["tasks"].append(text)
        data[user_id].pop("awaiting_task")
        save_data(data)
        await message.reply(f"✅ Task added: {text}")
    else:
        data[user_id]["awaiting_task"] = True
        save_data(data)
        await message.reply("👆 Click the Add Task button before sending a task.")

@dp.callback_query(F.data == "view_tasks")
async def view_tasks(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    user_tasks = data.get(user_id, {}).get("tasks", [])
    if not user_tasks:
        await callback.message.answer("📭 You have no tasks yet.")
    else:
        task_list = "\n".join([f"• {t}" for t in user_tasks])
        await callback.message.answer(f"📋 Your Tasks:\n{task_list}")

@dp.callback_query(F.data == "mark_done")
async def mark_done(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    if data[user_id].get("tasks"):
        finished = data[user_id]["tasks"].pop(0)
        data[user_id]["xp"] += 10

        today = datetime.now().date()
        last = data[user_id].get("last_done")
        if last:
            last_day = datetime.strptime(last, "%Y-%m-%d").date()
            if (today - last_day).days == 1:
                data[user_id]["streak"] += 1
            elif (today - last_day).days > 1:
                data[user_id]["streak"] = 1
        else:
            data[user_id]["streak"] = 1
        data[user_id]["last_done"] = today.strftime("%Y-%m-%d")
        save_data(data)
        await callback.message.answer(f"✅ Marked '{finished}' as done!\n+10 XP 🌟\n🔥 Streak: {data[user_id]['streak']}")
        if random.random() < 0.5:
            await callback.message.answer(get_tip())
    else:
        await callback.message.answer("😶 No tasks to mark done.")

@dp.callback_query(F.data == "show_tip")
async def show_tip(callback: types.CallbackQuery):
    await callback.message.answer(get_tip())

@dp.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("🚫 You don't have access to admin commands.")
    await message.answer("🛠 Admin panel coming soon. You’re verified ✅")

if __name__ == "__main__":
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())
