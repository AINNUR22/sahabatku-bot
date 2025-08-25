import os
import logging
import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID", "0"))
COUNSELOR_GROUP_ID = int(os.environ.get("COUNSELOR_GROUP_ID", "0"))

if not BOT_TOKEN:
    raise RuntimeError("❌ Missing BOT_TOKEN env var")
if GROUP_ID == 0:
    raise RuntimeError("❌ Missing or invalid GROUP_ID env var")
if COUNSELOR_GROUP_ID == 0:
    raise RuntimeError("❌ Missing or invalid COUNSELOR_GROUP_ID env var")

# --- Logging setup (helps debug on Render) ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# === Helper: Save student log in CSV ===
def save_user_log(user_id, first_name, last_name, username, category, message):
    file_exists = os.path.isfile("users.csv")
    with open("users.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["UserID", "FirstName", "LastName", "Username", "Category", "Message"])
        writer.writerow([user_id, first_name, last_name, username, category, message])

# === Helper: Save PRS report log in CSV ===
def save_prs_log(problem, report_content, prs_name, user_id, username, tg_name):
    file_exists = os.path.isfile("prs_reports.csv")
    with open("prs_reports.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Problem", "Content", "PRS_Name", "UserID", "Username", "TelegramName"])
        writer.writerow([problem, report_content, prs_name, user_id, username, tg_name])

# === Start command (student anonymous chat) ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ Perkembangan Sahsiah", callback_data="Perkembangan Sahsiah")],
        [InlineKeyboardButton("2️⃣ Kerjaya & Masa Depan", callback_data="Kerjaya & Masa Depan")],
        [InlineKeyboardButton("3️⃣ Isu Disiplin (Aduan)", callback_data="Isu Disiplin (Aduan)")],
        [InlineKeyboardButton("4️⃣ Psikososial & Kesejahteraan Minda", callback_data="Psikososial & Kesejahteraan Minda")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🤝 *Sahabatku: Safe Chatbox*\n\n"
        "🌸 Selamat datang! Ruang ini disediakan untuk anda meluahkan perasaan, "
        "berkongsi pandangan, atau membuat aduan secara *anonimous*.\n\n"
        "📜 Sila rujuk syarat & etika penggunaan Chatbox di pautan berikut:\n"
        "👉 https://form.jotform.com/212158615114448\n\n"
        "⚠️ Sekiranya anda memilih untuk tidak mengisi borang tersebut, "
        "anda dianggap *bersetuju* dengan semua terma & syarat yang telah ditetapkan.\n\n"
        "🔒 Kami menjamin kerahsiaan mesej anda. Identiti anda akan dirahsiakan, "
        "dan mesej hanya akan dipaparkan sebagai *Anonymous* dalam Chatbox ini.\n\n"
        "📝 Sila pilih kategori mesej anda dengan klik butang di bawah 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# === Callback for student category selection ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data
    context.user_data["category"] = category

    await query.edit_message_text(
        text=f"✅ Kategori dipilih: *{category}*\n\nSekarang sila taip mesej anda.",
        parse_mode="Markdown"
    )

# === Handle student messages ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "category" not in context.user_data:
        return  # Ignore messages before category selection

    user = update.effective_user
    message = update.message.text
    category = context.user_data.get("category", "Tidak Dipilih")

    save_user_log(user.id, user.first_name, user.last_name or "", user.username or "", category, message)

    forward_text = (
        f"📩 *Mesej Baru:*\n"
        f"Kategori: {category}\n"
        f"Mesej: {message}\n\n"
        f"👤 *Maklumat Penghantar:*\n"
        f"ID: {user.id}\n"
        f"Nama: {user.first_name} {user.last_name or ''}\n"
        f"Username: @{user.username if user.username else 'None'}"
    )
    await context.bot.send_message(chat_id=GROUP_ID, text=forward_text, parse_mode="Markdown")
    await update.message.reply_text("🤝 Sahabatku: ✅ Mesej anda telah diterima dan disimpan dengan selamat.")
    context.user_data.clear()

# === PRS Report Command ===
async def prs_report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ Masalah Keluarga", callback_data="Masalah Keluarga")],
        [InlineKeyboardButton("2️⃣ Isu Disiplin & Sahsiah", callback_data="Isu Disiplin & Sahsiah")],
        [InlineKeyboardButton("3️⃣ SELF-HARM & Perbuatan Ke Arah Itu", callback_data="SELF-HARM")],
        [InlineKeyboardButton("4️⃣ Masalah Akademik", callback_data="Masalah Akademik")],
        [InlineKeyboardButton("5️⃣ Penyalahgunaan Dadah", callback_data="Penyalahgunaan Dadah")],
        [InlineKeyboardButton("6️⃣ Masalah Sosial", callback_data="Masalah Sosial")],
        [InlineKeyboardButton("7️⃣ Lain-lain", callback_data="Lain-lain")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📌 *Portal Aduan PRS*\n\n"
        "Tujuan portal ini adalah untuk PRS/Peer Counselors menghantar laporan rahsia "
        "kepada counselor mengenai isu pelajar.\n\n"
        "📝 *Langkah-langkah pengisian:*\n"
        "1️⃣ Pilih jenis masalah dari senarai\n"
        "2️⃣ Taip kandungan laporan\n"
        "3️⃣ Masukkan nama PRS\n\n"
        "⚠️ Setiap submit akan dimasukkan di dalam rekod performance PRS beserta kemasukan ke "
        "data Amalan Baik MUID di aplikasi MOES. Semua data akan digunapakai untuk Anugerah Ikon PRS dan sebagainya.\n\n"
        "Terima kasih. Sila hantar dengan etika seorang PRS."
    )

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# === Callback for PRS Problem Choice ===
async def prs_problem_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    problem = query.data
    context.user_data["prs_problem"] = problem

    await query.edit_message_text(
        text=f"✅ Masalah dipilih: *{problem}*\n\nSekarang sila taip kandungan laporan anda.",
        parse_mode="Markdown"
    )

# === Handle PRS report messages ===
async def handle_prs_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "prs_problem" not in context.user_data:
        return  # Ignore unrelated messages

    user = update.effective_user
    message_text = update.message.text

    if "prs_stage" not in context.user_data:
        # First stage: Content
        context.user_data["prs_content"] = message_text
        context.user_data["prs_stage"] = "name"
        await update.message.reply_text("📝 Sila taip nama PRS yang menghantar laporan:")
        return

    if context.user_data.get("prs_stage") == "name":
        prs_name = message_text
        problem = context.user_data.get("prs_problem")
        report_content = context.user_data.get("prs_content")

        # Save to CSV
        save_prs_log(problem, report_content, prs_name, user.id, user.username or "", f"{user.first_name} {user.last_name or ''}")

        # Send full info to counselor group
        forward_text = (
            f"📩 *Laporan PRS Baru*\n"
            f"Masalah: {problem}\n"
            f"Kandungan Laporan: {report_content}\n"
            f"Nama PRS: {prs_name}\n\n"
            f"👤 *Maklumat Penghantar (Rahsia untuk counselor)*\n"
            f"ID: {user.id}\n"
            f"Nama Telegram: {user.first_name} {user.last_name
