
import requests
from config import TOKEN, CHAT_ID

def send_alert(name, price, url):
    message = f"🎲 *{name}* nuovo minimo storico: {price:.2f}€!\n🔗 {url}"
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except Exception as e:
        print(f"[Errore Telegram] {e}")
