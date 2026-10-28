import logging
import gspread
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Logging
logging.basicConfig(level=logging.INFO)

# Telegram Bot Token
BOT_TOKEN = '7627198915:AAGtXJ0nAhoOSMmm46VIHa3qeLTlesUiCQQ'

# Spreadsheet ID
SPREADSHEET_ID = '10c2nljfz0AhtXnFZCgm8XWS-Nw8spqREFumzhZQPUJc'
TOPOLOGI_SPREADSHEET_ID = '1KS4cDTBizUfU0d2jJnGfiCLWJkDzLIwO0jcVmcW8lN0'  # Gunakan ID file, bukan GID

# Setup GSpread
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_gspread = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds_gspread)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Sheet1")

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Selamat datang!\nKetik nama ODP untuk mencari lokasi, atau ketik /topologi untuk melihat diagram topologi.")

# Cari ODP
def cari_odp(keyword):
    data = sheet.get_all_values()
    hasil = []

    for row in data[5:]:  # Melewati header
        if len(row) < 15:
            continue
        if keyword.lower() in row[10].lower():
            try:
                lat = row[13].replace("\u00b0", "").replace(",", ".").strip()
                lon = row[14].replace("\u00b0", "").replace(",", ".").strip()
                lat = float(lat)
                lon = float(lon)
            except:
                continue

            hasil.append({
                'nama_odp': row[10],
                'qr_code': row[9],
                'alamat': row[12],
                'panel_in': f"{row[0]} / {row[1]} / {row[2]}",
                'panel_out': f"{row[3]} / {row[4]} / {row[5]}",
                'distribusi': f"Ke-{row[6]} | Kap: {row[7]} | Core: {row[8]}",
                'lat': lat,
                'lon': lon
            })
    return hasil

# Pesan user
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text.strip()
    data_list = cari_odp(keyword)

    if not data_list:
        await update.message.reply_text("ODP tidak ditemukan.")
        return

    for data in data_list:
        text = (
            f"[ODP] <b>{data['nama_odp']}</b>\n"
            f"[QR] QR Code: {data['qr_code']}\n"
            f"[Alamat] {data['alamat']}\n\n"
            f"[Panel IN] {data['panel_in']}\n"
            f"[Panel OUT] {data['panel_out']}\n"
            f"[Distribusi] {data['distribusi']}"
        )
        maps_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
        button = InlineKeyboardButton("Lihat di Google Maps", url=maps_url)

        await update.message.reply_text(text, parse_mode='HTML')
        await update.message.reply_location(
            latitude=data['lat'],
            longitude=data['lon'],
            reply_markup=InlineKeyboardMarkup([[button]])
        )

# Kirim topologi via Drive API
async def kirim_topologi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        creds = service_account.Credentials.from_service_account_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build('drive', 'v3', credentials=creds)

        # Export ke PDF
        request = service.files().export_media(fileId=TOPOLOGI_SPREADSHEET_ID, mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        await update.message.reply_document(document=InputFile(fh, filename="topologi.pdf"))

    except Exception as e:
        logging.exception("Gagal mengunduh file PDF:")
        await update.message.reply_text("Gagal mengambil file topologi.")

# Main Bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("topologi", kirim_topologi))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
