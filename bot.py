import asyncio
import json
import random
import shutil
import os
import glob
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
ADMIN_ID = 5480597971
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

# --- SAFE USER CREATION ---
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
            "lang": "en",
            "extra_title": ""   # ✅ for custom titles
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
}  # (keep your existing TEXTS here, unchanged)

# ===============================
# ✅ MOTIVATIONAL MESSAGES & TIPS
# ===============================

MOTIVATIONS = [
    "🔥 Keep pushing, you're doing amazing!",
    "💪 Small steps every day lead to big success.",
    "🚀 You’re on your way to greatness!",
    "🌟 Consistency is key, stay focused!",
    "🏆 Every completed task is a victory!",
    "✨ Progress, not perfection, is what matters.",
    "🎯 Stay sharp, one task at a time!",
    "🚴‍♂️ Momentum builds success – keep moving!",
    "⏳ Don’t wait for the perfect moment, make it now!",
    "🌄 Every day is a new chance to improve yourself!"
]

TIPS = [
    "💡 Tip: Stay consistent!",
    "💡 Tip: Focus on one task at a time!",
    "💡 Tip: Review your goals daily!"
]

# --- Russian Versions ---
MOTIVATIONS_RU = [
    "🔥 Продолжай в том же духе, ты молодец!",
    "💪 Маленькие шаги каждый день ведут к успеху.",
    "🚀 Ты на пути к великим достижениям!",
    "🌟 Последовательность – ключ к успеху!",
    "🏆 Каждая выполненная задача – победа!",
    "✨ Прогресс важнее совершенства.",
    "🎯 Сосредоточься на одной цели за раз!",
    "🚴‍♂️ Движение вперёд приводит к успеху!",
    "⏳ Не жди идеального момента, действуй сейчас!",
    "🌄 Каждый день — новая возможность стать лучше!"
]

TIPS_RU = [
    "💡 Совет: Будь последовательным!",
    "💡 Совет: Сосредоточься на одной задаче!",
    "💡 Совет: Пересматривай свои цели каждый день!"
]

# ✅ Helper functions to get random motivation or tip
def get_motivation(lang: str) -> str:
    """Return a random motivational message based on language."""
    return random.choice(MOTIVATIONS_RU) if lang == "ru" else random.choice(MOTIVATIONS)

def get_tip(lang: str) -> str:
    """Return a random tip based on language."""
    return random.choice(TIPS_RU) if lang == "ru" else random.choice(TIPS)


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
        return "🗽 Productivity Legend"

# --- XP SYSTEM & STREAKS ---
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

# ===============================
# ✅ NEW: BACKUP FEATURE
# ===============================
def cleanup_old_backups(keep=7):
    """Keep only the most recent `keep` backup files."""
    backups = sorted(glob.glob("backup_*.json"))
    while len(backups) > keep:
        os.remove(backups[0])  # delete oldest
        backups.pop(0)

def create_backup():
    """Create a timestamped backup and clean old ones."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.json"
    shutil.copy(DATA_FILE, backup_file)
    cleanup_old_backups()  # ✅ ensures only last 7 backups are kept
    return backup_file

@dp.message(Command("backup"))
async def backup_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ You are not authorized.")
    try:
        backup_path = create_backup()
        await message.answer("✅ Backup created, sending...")
        await bot.send_document(ADMIN_ID, types.FSInputFile(backup_path))
    except Exception as e:
        await message.answer(f"⚠️ Backup failed: {e}")

# --- KEYBOARDS ---
def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANGS["en"], callback_data="lang:en")],
        [InlineKeyboardButton(text=LANGS["ru"], callback_data="lang:ru")]
    ])

def main_kb(lang="en"):
    # ✅ updated to use language-specific buttons
    b = TEXTS[lang]["buttons"] if "buttons" in TEXTS[lang] else {
        "add": "➕ Add Task","list":"📋 List Tasks","done":"✅ Mark Done",
        "report":"📊 Daily Report","profile":"👤 Profile","leaderboard":"🏅 Leaderboard"
    }
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=b["add"]), KeyboardButton(text=b["list"])],
        [KeyboardButton(text=b["done"]), KeyboardButton(text=b["report"])],
        [KeyboardButton(text=b["profile"]), KeyboardButton(text=b["leaderboard"])]
    ], resize_keyboard=True)

# --- GLOBAL BROADCAST ---
async def send_global_message(text):
    for uid in list(DATA["users"].keys()):
        try:
            await bot.send_message(uid, text)
        except:
            pass

# ===============================
# ✅ NEW: TASK DEADLINES & REMINDERS
# ===============================
async def check_reminders():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz)

        for uid, u in DATA["users"].items():
            for t in u["tasks"]:
                if isinstance(t, dict) and "deadline" in t:
                    try:
                        dl = tz.localize(datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M"))
                        diff = (dl - now).total_seconds()

                        # Ensure reminders_sent flag exists
                        if "reminders_sent" not in t:
                            t["reminders_sent"] = 0

                        # Send 1 hour reminder
                        if 0 < diff <= 3600 and t["reminders_sent"] == 0:
                            await bot.send_message(int(uid), f"⏰ <b>Reminder:</b> '{t['text']}' is due in 1 hour!")
                            t["reminders_sent"] = 1
                            save_data()

                        # Send 10 minute reminder
                        elif 0 < diff <= 600 and t["reminders_sent"] == 1:
                            await bot.send_message(int(uid), f"⚠️ <b>Hurry up!</b> '{t['text']}' is due in 10 minutes!")
                            t["reminders_sent"] = 2
                            save_data()

                    except Exception as e:
                        print(f"[Reminder Error] {e}")

        await asyncio.sleep(60)  # check every minute


MORNING_IMAGE = "media/morning.jpg"

# --- MOTIVATIONAL REMINDERS ---
async def scheduled_motivation():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now in ["08:00", "14:00"]:
            for uid, user in DATA["users"].items():
                lang = user.get("lang", "en")
                msg = ("🌅 Утро! Начни день продуктивно!" if lang == "ru" and now == "08:00" else
                       "🌅 Good morning! Start your day strong!" if now == "08:00" else
                       "⏳ Держись, день ещё не закончен!" if lang == "ru" else
                       "⏳ Keep going, the day is not over yet!")
                await bot.send_message(uid, msg + "\n" + get_tip(lang))
            await asyncio.sleep(60)
        await asyncio.sleep(30)

async def send_morning_motivation():
    """Send a morning motivation image with caption to all users."""
    caption = "🌅 Good morning! \nStart your day strong and stay productive!🎐 "

    for uid in list(DATA["users"].keys()):
        try:
            if os.path.exists(MORNING_IMAGE):
                await bot.send_photo(int(uid), types.FSInputFile(MORNING_IMAGE), caption=caption)
            else:
                await bot.send_message(int(uid), "🌅 Good morning! (No image found today)")
        except Exception as e:
            print(f"[Morning Motivation Error] {e}")

async def scheduled_morning_images():
    """Scheduler to send the image at 07:00 every day."""
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.now(tz).strftime("%H:%M")
        if now == "07:00":
            await send_morning_motivation()
            await asyncio.sleep(60)  # wait a minute to avoid duplicate sends
        await asyncio.sleep(30)        


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
        return await message.answer(TEXTS[lang]["no_tasks"])

    task_lines = []
    for i, t in enumerate(user["tasks"], 1):
        if isinstance(t, dict):
            # Format deadline nicely
            dl = datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
            formatted = dl.strftime("%d %b, %H:%M")
            task_lines.append(f"{i}. {t['text'].upper()} – ⏳ {formatted}")
        else:
            task_lines.append(f"{i}. {str(t).upper()}")

    await message.answer("📝 <b>Your Tasks:</b>\n" + "\n".join(task_lines))


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

# --- ADMIN PANEL COMMANDS ---
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🔧 <b>Admin Panel</b>\nCommands:\n/broadcast <text>\n/addxp <user_id> <amount>\n/resetuser <user_id>\n/listusers")

@dp.message(Command("listusers"))
async def list_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = "\n".join([f"{u['name']} ({uid}) – {u['xp']} XP" for uid, u in DATA["users"].items()])
    await message.answer("👥 <b>Users:</b>\n" + (users if users else "No users."))

@dp.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return await message.answer("❌ Usage: /broadcast <text>")
    await send_global_message("📢 <b>Admin Broadcast:</b>\n" + text)
    await message.answer("✅ Broadcast sent.")

@dp.message(Command("addxp"))
async def admin_add_xp(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 3:
        return await message.answer("❌ Usage: /addxp <user_id> <amount>")
    uid, amount = parts[1], int(parts[2])
    if uid not in DATA["users"]:
        return await message.answer("❌ User not found.")
    DATA["users"][uid]["xp"] += amount
    save_data()
    await message.answer(f"✅ Added {amount} XP to {DATA['users'][uid]['name']}.")

@dp.message(Command("resetuser"))
async def reset_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("❌ Usage: /resetuser <user_id>")
    uid = parts[1]
    if uid in DATA["users"]:
        DATA["users"][uid] = get_or_create_user(uid, "ResetUser")
        save_data()
        await message.answer("✅ User reset.")
    else:
        await message.answer("❌ User not found.")

# ✅ New: Assign Titles
@dp.message(Command("settitle"))
async def set_title_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Not authorized.")
    try:
        _, uid, *title = message.text.split(" ")
        title = " ".join(title)
        if uid not in DATA["users"]:
            return await message.answer("❌ User not found.")
        DATA["users"][uid]["extra_title"] = title
        save_data()
        await message.answer(f"✅ Title '{title}' assigned to {DATA['users'][uid]['name']}")
    except:
        await message.answer("❌ Usage: /settitle <user_id> <title>")

# --- LEADERBOARD with TITLES & DECORATED NAMES ---
@dp.message(lambda m: m.text and "Leaderboard" in m.text)
async def leaderboard(message: Message):
    try:
        user = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
        lang = user["lang"]

        # Sort users by XP, take top 10
        users_sorted = sorted(DATA["users"].values(), key=lambda u: u.get("xp", 0), reverse=True)[:10]

        board_lines = []
        for i, u in enumerate(users_sorted, 1):
            name = u.get("name", "Unknown")
            title = u.get("extra_title", "").strip()
            xp = u.get("xp", 0)
            rank = get_rank(xp)

            # ⚜️ decorate name, add title if available
            display_name = f" {name} "
            title_part = f" | ⚜️ {title} ⚜️" if title else ""
            board_lines.append(f"{i}. {display_name}{title_part} – {xp} XP ({rank})")

        board = "\n".join(board_lines) if board_lines else "📭 No users yet."
        board_safe = board.replace("<", "&lt;").replace(">", "&gt;")

        ranks_info = (
            "\n\n<b>Ранги:</b>\n🎯 Новичок &lt;200 XP\n⚡ Достигающий 200–499 XP\n🔥 Уничтожитель задач 500–1199 XP\n🏆 Мастер 1200–2499 XP\n🗽 Легенда 2500+ XP"
            if lang == "ru" else
            "\n\n<b>Ranks:</b>\n🎯 Rookie &lt;200 XP\n⚡ Achiever 200–499 XP\n🔥 Crusher 500–1199 XP\n🏆 Master 1200–2499 XP\n🗽 Legend 2500+ XP"
        )

        await message.answer(TEXTS[lang]["leaderboard"].format(board_safe) + ranks_info)

    except Exception as e:
        await message.answer(f"⚠️ Leaderboard error: {e}")




# --- CATCH-ALL ---
@dp.message()
async def catch_all(message: Message):
    u = get_or_create_user(str(message.from_user.id), message.from_user.first_name)
    lang = u["lang"]
    txt = message.text.strip()

    # === DEADLINE STEP ===
    if u.get("awaiting_deadline"):
        raw = txt
        task_text = u.pop("pending_task", None)

        if not task_text:
            u.pop("awaiting_deadline", None)
            return await message.answer("⚠️ No task is waiting for a deadline.")

        # User chooses NO deadline
        if raw == "0":
            u["tasks"].append(task_text.upper())
            u.pop("awaiting_deadline", None)
            save_data()
            return await message.answer(f"🆕 Task added: <b>{task_text.upper()}</b> (No deadline)")

        # User enters hours
        try:
            hours = int(raw)
            if hours < 1 or hours > 24:
                raise ValueError
            deadline = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
            u["tasks"].append({"text": task_text.upper(), "deadline": deadline, "reminders_sent": 0})
            u.pop("awaiting_deadline", None)
            save_data()
            return await message.answer(f"🆕 Task added with deadline: <b>{deadline}</b>")
        except:
            return await message.answer("⚠️ Send a number between 1–24 (hours) or 0 for no deadline.")

    # === ADD TASK STEP ===
    if u.get("awaiting_task"):
        u.pop("awaiting_task", None)
        u["pending_task"] = txt
        u["awaiting_deadline"] = True
        save_data()
        return await message.answer("⏳ How many hours until the deadline? (1–24) or 0 for no deadline")

    # === MARK TASK DONE ===
    if txt.isdigit() and u["tasks"]:
        idx = int(txt) - 1
        if 0 <= idx < len(u["tasks"]):
            t = u["tasks"].pop(idx)
            task_name = t["text"] if isinstance(t, dict) else t
            u["completed"] += 1
            xp_msg = add_xp(u, 2)
            update_streak(u)
            save_data()
            return await message.answer(f"✅ Done: <b>{task_name}</b>\n{xp_msg}")
        return await message.answer(TEXTS[lang]["invalid_number"])

    # === FALLBACK ===
    await message.answer("ℹ️ Use buttons or commands to interact.")



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
    print("✅ Bot running with deadlines, backup & titles...")
    asyncio.create_task(scheduled_reports())
    asyncio.create_task(scheduled_motivation())
    asyncio.create_task(scheduled_morning_images())
    asyncio.create_task(check_reminders())  # ✅ start reminder loop
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
