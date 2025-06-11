from telegram import Bot
from telegram.ext import Updater, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging
import requests

# Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Ganti dengan token milikmu
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = None  # Ini nanti diisi otomatis saat kamu kirim /start ke bot

# Jadwal kegiatan harian default
jadwal_kegiatan = [
    ("04:30", "Bangun dan salat Subuh 🌅"),
    ("05:00", "Olahraga ringan 30 menit 💪"),
    ("06:00", "Sarapan sehat 🍽️"),
    ("06:30", "Berangkat kerja 🚗"),
    ("17:00", "Pulang kerja 🚘"),
    ("19:00", "Waktu belajar/upgrade skill 📚"),
    ("20:30", "Persiapan tidur 💼"),
    ("21:00", "Tidur malam 💏")
]

# Fungsi untuk ambil waktu salat otomatis
def ambil_waktu_salat():
    try:
        url = "https://api.aladhan.com/v1/timingsByCity?city=Jakarta&country=Indonesia&method=2"
        response = requests.get(url)
        data = response.json()["data"]["timings"]
        waktu_salat = [
            (data["Fajr"][:5], "Salat Subuh 🌅"),
            (data["Dhuhr"][:5], "Salat Dzuhur 🏤"),
            (data["Asr"][:5], "Salat Ashar 🏤"),
            (data["Maghrib"][:5], "Salat Maghrib 🏤"),
            (data["Isha"][:5], "Salat Isya 🏤")
        ]
        return waktu_salat
    except Exception as e:
        logging.error(f"Gagal ambil waktu salat: {e}")
        return []

# Fungsi untuk mengirim pesan
def kirim_pesan(context: CallbackContext, message=None):
    if CHAT_ID:
        context.bot.send_message(chat_id=CHAT_ID, text=message)

# Fungsi untuk dijalankan saat /start
from telegram.ext import CommandHandler, CallbackContext

def start(update, context):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    update.message.reply_text("Bot pengingat harian sudah aktif! ⏰")

    # Ambil waktu salat terbaru
    waktu_salat = ambil_waktu_salat()
    semua_jadwal = jadwal_kegiatan + waktu_salat

    # Jadwalkan semua pengingat
    for waktu, pesan in semua_jadwal:
        jam, menit = map(int, waktu.split(":"))
        scheduler.add_job(
            kirim_pesan,
            trigger='cron',
            hour=jam,
            minute=menit,
            args=[context],
            kwargs={'message': pesan},
            timezone='Asia/Jakarta'
        )

def stop(update, context):
    scheduler.remove_all_jobs()
    update.message.reply_text("Semua pengingat telah dihentikan ❌")

# Fungsi untuk menangani perintah /jadwal
def jadwal(update, context):
    pesan = "📅 Jadwal Harian Kamu:\n\n"
    semua_jadwal = jadwal_kegiatan + ambil_waktu_salat()
    semua_jadwal.sort()
    for waktu, aktivitas in semua_jadwal:
        pesan += f"{waktu} - {aktivitas}\n"
    update.message.reply_text(pesan)

# Inisialisasi bot dan scheduler
updater = Updater(token=TOKEN, use_context=True)
dp = updater.dispatcher
scheduler = BackgroundScheduler()
scheduler.start()

# Tambahkan command handler
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("stop", stop)) 
dp.add_handler(CommandHandler("jadwal", jadwal))

# Jalankan bot
updater.start_polling()
updater.idle()
