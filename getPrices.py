import requests
import re
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = "7431941125:AAH7woPQaIlfOT_sUBJVhehcOSletH_ZsIY"
LISTA_PATH = "Lista.json"

def get_price_dungeondice(url):
    if not url:
        return None
    try:
        html = requests.get(url, timeout=10).text
        if re.search(r'<span[^>]*>remove_shopping_cart<\/span>\s*<span>(.*?)<\/span>', html):
            return None
        if re.search(r'<span[^>]*>Preordina<\/span>', html, re.I):
            return None

        m = re.search(r'<div[^>]*class=["\']display-price["\'][^>]*>Prezzo(?: Speciale)?:\s*(\d+,\d+)', html)
        if m:
            return float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[Errore DungeonDice] {url} → {e}")
    return None

def get_price_magicmerchant(url):
    if not url:
        return None
    try:
        html = requests.get(url, timeout=10).text
        if re.search(r'<p class="outofstock availability verbose availability-message">', html):
            return None
        m = re.search(r'<p class="price_color">(\d{1,3},\d{2})', html)
        if m:
            return float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[Errore MagicMerchant] {url} → {e}")
    return None

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
    
    trovato = False
    for gioco in giochi:
        if gioco["name"].lower() == nome_ricerca:
            trovato = True
            messaggio = f"Prezzi attuali per *{gioco['name']}*:\n"
            for url in gioco["links"]:
                if "dungeondice.it" in url:
                    prezzo = get_price_dungeondice(url)
                    sito = "DungeonDice"
                elif "magicmerchant.it" in url:
                    prezzo = get_price_magicmerchant(url)
                    sito = "MagicMerchant"
                else:
                    prezzo = None
                    sito = "Sito sconosciuto"
                
                if prezzo is not None:
                    messaggio += f"- {sito}: {prezzo:.2f} €\n{url}\n"
                else:
                    messaggio += f"- {sito}: non disponibile\n{url}\n"
            
            update.message.reply_text(messaggio, parse_mode="Markdown", disable_web_page_preview=True)
            break
    
    if not trovato:
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
