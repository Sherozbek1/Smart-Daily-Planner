import asyncio
import json
import random
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# --- BOT CONFIG ---
BOT_TOKEN = "8387365932:AAGmMO0h2TVNE-bKpHME22sqWApfm7_UW6c"
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# --- DATA STORAGE ---
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

# --- UTIL: SAFE USER CREATION ---
def get_or_create_user(uid, name="Unknown"):
    if uid not in DATA["users"]:
        DATA["users"][uid] = {
            "user_id": uid,
            "name": name,
            "tasks": [],
            "completed": 0,
            "streak": 0,
            "last_active": "",
            "xp": 0,
            "lang": "en"
        }
        save_data()
    return DATA["users"][uid]

# --- LANGUAGES ---
LANGS = {"en": "🇬🇧 English", "ru": "🇷🇺 Russian"}

TEXTS = {
    "en": {
        "welcome": "👋 Welcome to <b>Smart Daily Planner</b>!\n\nI will help you stay productive with:\n"
                   "✅ Tasks\n🔥 Streaks\n⭐ XP & Ranks\n💡 Motivational tips\n\nChoose your language to continue:",
        "intro": "📚 <b>How to use:</b>\n"
                 "• ➕ Add Task – add new task\n"
                 "• 📋 List Tasks – view all tasks\n"
                 "• ✅ Mark Done – mark a task as completed\n"
                 "• 📊 Daily Report – get your progress\n"
                 "• 👤 Profile – view XP, streak, and stats\n"
                 "• 🏅 Leaderboard – see top users",
        "profile": "👤 <b>Profile</b>\n🆔 ID: <code>{}</code>\n🏷️ Name: {}\n✅ Completed: {}\n🔥 Streak: {} days\n⭐ XP: {} ({})",
        "task_added": "🆕 Task added: {}",
        "no_tasks": "📭 You have no tasks.",
        "mark_done": "Send the number of the task you completed:\n{}",
        "task_done": "✅ Task marked as done: {}",
        "invalid_number": "❌ Invalid task number.",
        "daily_report": "📊 <b>Daily Report</b>\n✅ Completed: {}\n📌 Pending: {}\n🎯 Completion: {}%\n🔥 Streak: {} days\n⭐ XP: {} ({})\n\n💡 {}",
        "leaderboard": "🏅 <b>Leaderboard – Top 10</b>\n{}"
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в <b>Умный Планировщик</b>!\n\nЯ помогу вам быть продуктивным:\n"
                   "✅ Задачи\n🔥 Серии\n⭐ Опыт и Ранги\n💡 Мотивация\n\nВыберите язык для продолжения:",
        "intro": "📚 <b>Как использовать:</b>\n"
                 "• ➕ Добавить задачу – новая задача\n"
                 "• 📋 Список задач – посмотреть задачи\n"
                 "• ✅ Завершить – отметить задачу выполненной\n"
                 "• 📊 Отчет – ваш прогресс\n"
                 "• 👤 Профиль – опыт, серия, статистика\n"
                 "• 🏅 Таблица лидеров – топ пользователей",
        "profile": "👤 <b>Профиль</b>\n🆔 ID: <code>{}</code>\n🏷️ Имя: {}\n✅ Выполнено: {}\n🔥 Серия: {} дней\n⭐ XP: {} ({})",
        "task_added": "🆕 Задача добавлена: {}",
        "no_tasks": "📭 У вас нет задач.",
        "mark_done": "Отправьте номер выполненной задачи:\n{}",
        "task_done": "✅ Задача выполнена: {}",
        "invalid_number": "❌ Неверный номер задачи.",
        "daily_report": "📊 <b>Отчет за день</b>\n✅ Выполнено: {}\n📌 Осталось: {}\n🎯 Прогресс: {}%\n🔥 Серия: {} дней\n⭐ XP: {} ({})\n\n💡 {}",
        "leaderboard": "🏅 <b>Топ 10 пользователей</b>\n{}"
    }
}

# --- MOTIVATIONS & TIPS ---
MOTIVATIONS = [
    "🔥 Keep pushing, you're doing amazing!",
    "💪 Small steps every day lead to big success.",
    "🚀 You’re on your way to greatness!",
    "🌟 Consistency is key, stay focused!",
    "🏆 Every completed task is a victory!"
]
TIPS = ["💡 Tip: Stay consistent!", "💡 Tip: Focus on one task at a time!", "💡 Tip: Review your goals daily!"]

# --- RANK SYSTEM ---
def get_rank(xp):
    if xp < 200:
        return "🎯 Rookie Planner"
    elif xp < 500:
        return "⚡ Focused Achiever"
    elif xp < 1200:
        return "🔥 Task Crusher"
    elif xp < 2500:
        return "🏆 Consistency Master"
    else:
        return "🌟 Productivity Legend"

# --- KEYBOARDS ---
def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANGS["en"], callback_data="lang:en")],
        [InlineKeyboardButton(text=LANGS["ru"], callback_data="lang:ru")]
    ])

def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Add Task"), KeyboardButton(text="📋 List Tasks")],
        [KeyboardButton(text="✅ Mark Done"), KeyboardButton(text="📊 Daily Report")],
        [KeyboardButton(text="👤 Profile"), KeyboardButton(text="🏅 Leaderboard")]
    ], resize_keyboard=True)

# --- XP SYSTEM ---
def add_xp(user, amount):
    today = datetime.now().strftime("%Y-%m-%d")
    if user.get("xp_date") != today:
        user["xp_date"] = today
        user["xp_today"] = 0
    if user["xp_today"] >= 20:
        return "⚠️ Daily XP cap reached."
    to_add = min(amount, 20 - user["xp_today"])
    user["xp"] += to_add
    user["xp_today"] += to_add
    return f"✨ +{to_add} XP!"

# --- STREAK UPDATE ---
def update_streak(user):
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_active"] != today:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        user["streak"] = user["streak"] + 1 if user["last_active"] == yesterday else 1
        user["last_active"] = today
        bonus_msg = ""
        if user["streak"] % 7 == 0:
            add_xp(user, 5)
            bonus_msg += "\n🏅 Weekly streak +5 XP!"
        week_bonus = min(user["streak"] // 7, 7)
        if week_bonus > 0:
            add_xp(user, week_bonus)
            bonus_msg += f"\n🔥 Streak bonus +{week_bonus} XP!"
        user["bonus_msg"] = bonus_msg

def random_tip():
    return random.choice(TIPS) if random.random() < 0.3 else ""

# --- COMMAND HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: Message):
    uid = str(message.from_user.id)
    get_or_create_user(uid, message.from_user.first_name)
    await message.answer(TEXTS["en"]["welcome"], reply_markup=lang_kb())

@dp.callback_query(lambda c: c.data.startswith("lang:"))
async def set_lang(callback: types.CallbackQuery):
    uid = str(callback.from_user.id)
    user = get_or_create_user(uid, callback.from_user.first_name)
    user["lang"] = callback.data.split(":")[1]
    save_data()
    await callback.message.answer(TEXTS[user["lang"]]["intro"], reply_markup=main_kb())
    await callback.answer()

# --- BUTTON HANDLERS ---
@dp.message(lambda m: m.text == "➕ Add Task")
async def ask_task(message: Message):
    user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
    user["awaiting_task"] = True
    await message.answer("✍️ Send the task text:")

@dp.message(lambda m: m.text == "📋 List Tasks")
async def list_tasks(message: Message):
    user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
    lang = user["lang"]
    if not user["tasks"]:
        await message.answer(TEXTS[lang]["no_tasks"])
    else:
        await message.answer("📝 " + "\n".join([f"{i+1}. {t}" for i, t in enumerate(user["tasks"])]))

@dp.message(lambda m: m.text == "✅ Mark Done")
async def mark_done_prompt(message: Message):
    user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
    lang = user["lang"]
    if not user["tasks"]:
        await message.answer(TEXTS[lang]["no_tasks"])
        return
    task_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(user["tasks"])])
    await message.answer(TEXTS[lang]["mark_done"].format(task_list))

@dp.message(lambda m: m.text == "📊 Daily Report")
async def daily_report(message: Message):
    user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
    lang = user["lang"]
    total = len(user["tasks"])
    completed = user["completed"]
    percent = int((completed / (completed + total)) * 100) if (completed + total) else 0
    mot = random.choice(MOTIVATIONS)
    tip = random.choice(TIPS)
    await message.answer(TEXTS[lang]["daily_report"].format(completed, total, percent, user["streak"], user["xp"], get_rank(user["xp"]), mot + "\n" + tip))

@dp.message(lambda m: m.text == "👤 Profile")
async def profile(message: Message):
    user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
    lang = user["lang"]
    await message.answer(TEXTS[lang]["profile"].format(user["user_id"], user["name"], user["completed"], user["streak"], user["xp"], get_rank(user["xp"])))

# --- LEADERBOARD (SAFE) ---
# --- LEADERBOARD (SAFE, NO XP REQUIREMENTS, NO DUMMIES) ---
@dp.message(lambda m: m.text and "Leaderboard" in m.text)
async def leaderboard(message: Message):
    try:
        user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
        lang = user["lang"]

        # Sort users by XP, max 10
        users_sorted = sorted(DATA["users"].values(), key=lambda u: u.get("xp", 0), reverse=True)[:10]
        board_lines = [
            f"{i}. {u.get('name','Unknown')} – {u.get('xp',0)} XP ({get_rank(u.get('xp',0))})"
            for i, u in enumerate(users_sorted, 1)
        ]
        board = "\n".join(board_lines) if board_lines else "📭 No users yet."
        board_safe = board.replace("<", "&lt;").replace(">", "&gt;")

        ranks_info = (
            "\n\n<b>Ранги:</b>\n🎯 Новичок &lt;200 XP\n⚡ Достигающий 200–499 XP\n🔥 Уничтожитель задач 500–1199 XP\n🏆 Мастер 1200–2499 XP\n🌟 Легенда 2500+ XP"
            if lang == "ru" else
            "\n\n<b>Ranks:</b>\n🎯 Rookie &lt;200 XP\n⚡ Achiever 200–499 XP\n🔥 Crusher 500–1199 XP\n🏆 Master 1200–2499 XP\n🌟 Legend 2500+ XP"
        )

        await message.answer(TEXTS[lang]["leaderboard"].format(board_safe) + ranks_info)

    except Exception as e:
        await message.answer(f"⚠️ Leaderboard error: {e}")



# --- CATCH-ALL ---
@dp.message()
async def catch_all(message: Message):
    user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
    lang = user["lang"]
    text = message.text.strip()

    if text.isdigit() and user["tasks"]:
        index = int(text) - 1
        if 0 <= index < len(user["tasks"]):
            task = user["tasks"].pop(index)
            user["completed"] += 1
            xp_msg = add_xp(user, 2)
            update_streak(user)
            bonus_msg = user.pop("bonus_msg", "")
            save_data()
            await message.answer(TEXTS[lang]["task_done"].format(task) + f"\n{xp_msg}{bonus_msg}\n" + random_tip())
        else:
            await message.answer(TEXTS[lang]["invalid_number"])
        return

    if user.get("awaiting_task"):
        user["tasks"].append(text)
        user.pop("awaiting_task")
        save_data()
        await message.answer(TEXTS[lang]["task_added"].format(text))
    else:
        await message.answer("ℹ️ Use buttons or commands to interact with the bot.")

# --- SCHEDULED REPORTS ---
async def scheduled_reports():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now == "21:00":
            for uid in list(DATA["users"].keys()):
                fake_msg = types.SimpleNamespace(from_user=types.User(id=int(uid), is_bot=False))
                await daily_report(fake_msg)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# --- MAIN ---
async def main():
    load_data()
    print("✅ Bot running with leaderboard fix and all features intact...")
    asyncio.create_task(scheduled_reports())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
