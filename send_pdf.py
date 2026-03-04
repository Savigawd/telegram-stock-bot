import requests
from datetime import datetime
import json
import os

# ================= CONFIG =================
BOT_TOKEN = "8005234810:AAH2-nxnqTypUl39D8xi-LhJuuHywH1hodU"
USERS_FILE = "users.json"
LOG_FILE = "scheduler_test.log"
# ==========================================


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


log("===== task started =====")

# -------- save user --------
def save_user(chat_id):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)

    if chat_id not in users:
        users.append(chat_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f)


def get_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# -------- collect users who pressed /start --------
try:
    updates = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
        timeout=10
    ).json()

    for result in updates.get("result", []):
        if "message" in result:
            chat_id = result["message"]["chat"]["id"]
            save_user(chat_id)

    log("users updated successfully")

except Exception as e:
    log(f"ERROR getting updates: {e}")


# -------- build today's PDF URL --------
today = datetime.today()
year = today.year
month = today.month
day = today.day

pdf_url = (
    f"https://cdn.efghermes.com/Retail/Technical%20Bulletin%20Report/"
    f"{year}/{month}/{day}/0/"
    f"THE%20TECHNICAL%20BULLETIN%20{day:02d}-{month:02d}-{year}.pdf"
)

log(f"PDF URL: {pdf_url}")

users = get_users()
log(f"users count: {len(users)}")

# -------- download PDF --------
try:
    response = requests.get(pdf_url, timeout=20)
except Exception as e:
    log(f"ERROR downloading PDF: {e}")
    response = None


# -------- send to all users --------
if response and response.status_code == 200:
    log("PDF found, sending to users")

    for chat_id in users:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={
                    "chat_id": chat_id,
                    "caption": "Technical Bulletin for today"
                },
                files={
                    "document": (
                        f"THE_TECHNICAL_BULLETIN_{day:02d}-{month:02d}-{year}.pdf",
                        response.content
                    )
                },
                timeout=20
            )
            log(f"sent PDF to {chat_id}")

        except Exception as e:
            log(f"ERROR sending to {chat_id}: {e}")

else:
    log("PDF NOT FOUND")

    for chat_id in users:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": f"PDF not found for today\n{pdf_url}"
                },
                timeout=10
            )
            log(f"sent not-found msg to {chat_id}")

        except Exception as e:
            log(f"ERROR sending error msg to {chat_id}: {e}")


log("===== task finished =====")
