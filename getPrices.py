import re, json, requests, os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("7431941125:AAH7woPQaIlfOT_sUBJVhehcOSletH_ZsIY")
LISTA_PATH = "Lista.json"

app = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

def get_price_dungeondice(url):
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

def get_price_fantasiastore(url):
    try:
        html = requests.get(url, timeout=10).text
        if 'data-stock="0"' in html:
            return None
        m = re.search(r'<div class="product-price">.*?(\d{1,3},\d{2})', html, re.S)
        if m:
            return float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[Errore FantasiaStore] {url} → {e}")
    return None

def get_price_uplay(url):
    try:
        html = requests.get(url, timeout=10).text
        if re.search(r'<div class="notOrderableText[^>]*">', html):
            return None
        if not re.search(r'<span class="shipping-info[^>]*">\s*disponibile', html, re.I):
            return None
        m = re.search(r'<span class="price fw-bold">\s*(\d{1,3},\d{2})', html) or \
            re.search(r'<div class="promo-price">\s*(\d{1,3},\d{2})', html)
        if m:
            return float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[Errore Uplay] {url} → {e}")
    return None

async def prezzo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Per favore usa: /prezzo <nome gioco>")
        return

    nome_ricerca = " ".join(context.args).lower()
    try:
        with open(LISTA_PATH, "r", encoding="utf-8") as f:
            giochi = json.load(f)
    except Exception as e:
        await update.message.reply_text("Errore nel leggere la lista giochi.")
        print(f"Errore JSON: {e}")
        return

    for gioco in giochi:
        if gioco["name"].lower() == nome_ricerca:
            messaggio = f"Prezzi attuali per *{gioco['name']}*:\n"
            for url in gioco["links"]:
                if "dungeondice.it" in url:
                    prezzo = get_price_dungeondice(url)
                    sito = "DungeonDice"
                elif "magicmerchant.it" in url:
                    prezzo = get_price_magicmerchant(url)
                    sito = "MagicMerchant"
                elif "fantasiastore.it" in url:
                    prezzo = get_price_fantasiastore(url)
                    sito = "FantasiaStore"
                elif "uplay.it" in url:
                    prezzo = get_price_uplay(url)
                    sito = "Uplay"
                else:
                    prezzo = None
                    sito = "Sito sconosciuto"

                if prezzo is not None:
                    messaggio += f"- {sito}: {prezzo:.2f} €\n{url}\n"
                else:
                    messaggio += f"- {sito}: non disponibile\n{url}\n"

            await update.message.reply_text(messaggio, parse_mode="Markdown", disable_web_page_preview=True)
            return

    await update.message.reply_text("Gioco non trovato nella lista. Controlla il nome.")

application.add_handler(CommandHandler("prezzo", prezzo_command))

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

if __name__ == "__main__":
    import asyncio
    asyncio.run(application.initialize())
    application.bot.set_webhook(f"https://TUA-APP-RENDER.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=10000)
