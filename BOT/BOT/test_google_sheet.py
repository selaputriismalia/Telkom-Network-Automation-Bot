import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Konfigurasi kredensial
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# ID spreadsheet kamu
SPREADSHEET_ID = "10c2nljfz0AhtXnFZCgm8XWS-Nw8spqREFumzhZQPUJc"
sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Sheet1")

# Ambil semua data
data = sheet.get_all_values()

# Tampilkan di terminal
for row in data:
    print(row)
