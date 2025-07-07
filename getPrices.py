import requests
import re
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import ContextTypes

import os
from aiohttp import web

TOKEN = os.environ.get("TOKEN")
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

def get_price_fantasiastore(url):
    if not url:
        return None
    try:
        html = requests.get(url, timeout=10).text
        if re.search(r'class="product-not-available"', html):
            return None
        m = re.search(r'<span[^>]*class="price"[^>]*>(\d{1,3},\d{2})\s*€</span>', html)
        if m:
            return float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[Errore FantasiaStore] {url} → {e}")
    return None

def get_price_uplay(url):
    if not url:
        return None
    try:
        html = requests.get(url, timeout=10).text
        if re.search(r'<div class="notOrderableText[^>]*">\s*(.*?)\s*</div>', html):
            return None
        availability = re.search(r'<span class="shipping-info[^>]*">\s*(.*?)\s*</span>', html)
        if availability and "disponibile" not in availability.group(1).lower():
            return None
        price = re.search(r'<span class="price fw-bold">\s*(\d{1,3},\d{2})', html)
        promo_price = re.search(r'<div class="promo-price">\s*(\d{1,3},\d{2})', html)
        prezzo_finale = promo_price or price
        if prezzo_finale:
            prezzo_pulito = prezzo_finale.group(1).replace(",", ".")
            return float(prezzo_pulito)
    except Exception as e:
        print(f"[Errore UPlay] {url} → {e}")
    return None

async def prezzo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
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
                elif "fantasiastore.it" in url:
                    prezzo = get_price_fantasiastore(url)
                    sito = "FantasiaStore"
                elif "uplay.com" in url or "store.ubi.com" in url:
                    prezzo = get_price_uplay(url)
                    sito = "UPlay"
                else:
                    prezzo = None
                    sito = "Sito sconosciuto"
                
                if prezzo is not None:
                    messaggio += f"- {sito}: {prezzo:.2f} €\n{url}\n"
                else:
                    messaggio += f"- {sito}: non disponibile\n{url}\n"
            
            await update.message.reply_text(messaggio, parse_mode="Markdown", disable_web_page_preview=True)
            break
    
    if not trovato:
        await update.message.reply_text("Gioco non trovato nella lista. Controlla il nome.")

async def handle_update(request):
    """Riceve POST da Telegram webhook, elabora update e risponde."""
    app = request.app['bot_app']
    try:
        update = Update.de_json(await request.json(), app.bot)
        await app.update_queue.put(update)
        return web.Response(text="ok")
    except Exception as e:
        print(f"Errore handle_update: {e}")
        return web.Response(status=500)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("prezzo", prezzo_command))
    print("Bot webhook pronto...")

    web_app = web.Application()
    web_app['bot_app'] = app
    web_app.router.add_post(f"/{TOKEN}", handle_update)  # Telegram POST webhook path

    # Porta e host Render (o usa 0.0.0.0 e PORT da env)
    port = int(os.environ.get("PORT", "8080"))
    host = "0.0.0.0"

    # Start webhook & aiohttp server
    app.run_webhook(
        listen=host,
        port=port,
        webhook_url=f"https://bgprices.onrender.com/{TOKEN}",
        webhook_path=f"/{TOKEN}",
        webhook_cert=None,  # se hai certificato SSL custom mettilo qui
        # certificato di solito gestito da Render con https automatico
        app=web_app
    )

if __name__ == "__main__":
    main()
