import requests
import re
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = "7431941125:AAH7woPQaIlfOT_sUBJVhehcOSletH_ZsIY"
LISTA_PATH = "Lista.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_price_dungeondice(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        if re.search(r'<span[^>]*>remove_shopping_cart<\/span>\s*<span>(.*?)<\/span>', html):
            return None
        if re.search(r'<span[^>]*>Preordina<\/span>', html, re.I):
            return None
        m = re.search(r'<div[^>]*class=["\']display-price["\'][^>]*>Prezzo(?: Speciale)?:\s*(\d+,\d+)', html)
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore DungeonDice] {url} → {e}")
        return None

def get_price_fantasiastore(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).content.decode("utf-8", errors="replace")
        disponibile = re.search(r'<i[^>]*class=["\']fa fa-circle-o-notch[^>]*>.*?</i>\s*(.*?)\s*</button>', html)
        if disponibile and "Aggiungi al carrello" not in disponibile.group(1):
            return None
        m = re.search(r'<span itemprop="price" class="product-price" content="(\d+\.\d+)">', html)
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore FantasiaStore] {url} → {e}")
        return None

def get_price_magicmerchant(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        if re.search(r'<p class="outofstock availability verbose availability-message">', html):
            return None
        m = re.search(r'<p class="price_color">(\d{1,3},\d{2})', html)
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore MagicMerchant] {url} → {e}")
        return None

def get_price_uplay(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        if re.search(r'<div class="notOrderableText[^>]*">\s*(.*?)\s*</div>', html):
            return None
        disponibile = re.search(r'<span class="shipping-info[^>]*">\s*(.*?)\s*</span>', html)
        if not disponibile or "disponibile" not in disponibile.group(1).lower():
            return None
        m = re.search(r'<span class="price fw-bold">\s*(\d{1,3},\d{2})', html) or \
            re.search(r'<div class="promo-price">\s*(\d{1,3},\d{2})', html)
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore Uplay] {url} → {e}")
        return None

SCRAPER_MAP = {
    "dungeondice.it": ("DungeonDice", get_price_dungeondice),
    "fantasiastore.it": ("FantasiaStore", get_price_fantasiastore),
    "magicmerchant.it": ("MagicMerchant", get_price_magicmerchant),
    "uplay.it": ("Uplay", get_price_uplay)
}

def prezzo_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Per favore usa: /prezzo <nome gioco>")
        return
    
    nome_ricerca = " ".join(context.args).lower()

    try:
        with open(LISTA_PATH, "r", encoding="utf-8") as f:
            giochi = json.load(f)
    except Exception as e:
        update.message.reply_text("Errore nel leggere la lista giochi.")
        print(f"Errore JSON: {e}")
        return

    for gioco in giochi:
        if gioco["name"].lower() == nome_ricerca:
            messaggio = f"Prezzi attuali per *{gioco['name']}*:\n"
            for url in gioco["links"]:
                trovato = False
                for dominio, (nome_sito, scraper_func) in SCRAPER_MAP.items():
                    if dominio in url:
                        prezzo = scraper_func(url)
                        trovato = True
                        break
                if not trovato:
                    nome_sito = "Sito sconosciuto"
                    prezzo = None
                if prezzo is not None:
                    messaggio += f"- {nome_sito}: {prezzo:.2f} €\n{url}\n"
                else:
                    messaggio += f"- {nome_sito}: non disponibile\n{url}\n"
            update.message.reply_text(messaggio, parse_mode="Markdown", disable_web_page_preview=True)
            return

    update.message.reply_text("Gioco non trovato nella lista. Controlla il nome.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("prezzo", prezzo_command))
    print("Bot avviato...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
