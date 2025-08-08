import json
import csv
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from collections import defaultdict

COMMANDS_INFO = {
    "info": "Descrizione del bot",
    "prezzi": "Controlla i prezzi di un gioco: usa `/prezzi <nome>`",
    "storico": "Storico dei prezzi di un gioco: usa `/storico <nome>`",
    "store": "Mostra i giochi in cui uno store ha il prezzo più basso: usa `/store <nome_store>`"
}

# Funzione per ottenere i prezzi di un gioco
def get_prezzi_gioco(nome_gioco, filename="PrezziAttuali.json"):
    with open(filename, "r", encoding="utf-8") as f:
        dati = json.load(f)

    for gioco in dati:
        if gioco["name"].lower() == nome_gioco.lower():
            prezzi = gioco.get("prezzi", {})
            return sorted(
                [(store, info["price"], info["url"]) for store, info in prezzi.items()],
                key=lambda x: x[1]
            )
    return None

# Funzione per ottenere lo storico prezzi di un gioco
def get_storico_prezzi(nome_gioco: str) -> dict:
    storico = defaultdict(list)

    try:
        with open("storico_prezzi.csv", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["gioco"].lower() == nome_gioco.lower():
                    try:
                        raw_date = row["data"]
                        date_obj = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                        data = date_obj.strftime("%d/%m/%Y")
                    except Exception:
                        data = row["data"]

                    sito = row["sito"]
                    prezzo = row["prezzo"]
                    storico[sito].append((data, prezzo))

        return dict(storico)

    except FileNotFoundError:
        return {"errore": "File storico_prezzi.csv non trovato."}
    except Exception as e:
        return {"errore": str(e)}

# Funzione per gestire il comando /store
async def store_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Uso: /store <nome_store>")
        return

    store = context.args[0]

    try:
        with open("PrezziAttuali.json", "r", encoding="utf-8") as f:
            dati_json = json.load(f)
    except FileNotFoundError:
        await update.message.reply_text("⚠️ File PrezziAttuali.json non trovato.")
        return

    risultati = []
    for gioco in dati_json:
        prezzi = gioco.get("prezzi", {})
        if store in prezzi:
            min_price = min(p["price"] for p in prezzi.values())
            if prezzi[store]["price"] == min_price:
                risultati.append({
                    "name": gioco["name"],
                    "price": prezzi[store]["price"],
                    "url": prezzi[store]["url"]
                })

    if not risultati:
        await update.message.reply_text(f"Lo store '{store}' non ha il prezzo più basso per nessun gioco.")
        return

    response_lines = [f"Giochi per cui {store} ha il prezzo più basso:"]
    for item in risultati:
        response_lines.append(f"- {item['name']}: €{item['price']} ({item['url']})")

    await update.message.reply_text("\n".join(response_lines), disable_web_page_preview=True)

# Comando /storico
async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Scrivi il nome del gioco dopo /storico, es: /storico Scythe")
        return

    nome = " ".join(context.args)
    dati = get_storico_prezzi(nome)

    if "errore" in dati:
        await update.message.reply_text(f"⚠️ Errore: {dati['errore']}")
        return

    if not dati:
        await update.message.reply_text(f"Nessun dato trovato per *{nome}*", parse_mode="Markdown")
        return

    msg = f"*Storico prezzi per '{nome}'*\n"
    for store, records in dati.items():
        msg += f"\n📦 {store}:\n"
        for timestamp, prezzo in records[-5:]:
            msg += f"  - {timestamp}: {prezzo} €\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# Comando /commands
async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = "🤖 *Comandi disponibili:*\n\n"
    for cmd, desc in COMMANDS_INFO.items():
        testo += f"/{cmd} — {desc}\n"
    await update.message.reply_text(testo, parse_mode="Markdown")

# Comando /info
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot controlla i prezzi dei giochi da tavolo ogni ora "
        "e notifica l'utente se un gioco raggiunge il suo minimo storico."
    )

# Comando /prezzi
async def prezzi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Scrivi il nome del gioco dopo /prezzi, es: /prezzi Scythe")
        return
    
    nome_gioco = " ".join(context.args)
    risultati = get_prezzi_gioco(nome_gioco)

    if not risultati:
        await update.message.reply_text(f"Gioco '{nome_gioco}' non trovato.")
        return

    risposta = f"Prezzi per *{nome_gioco}*:\n"
    for store, prezzo, url in risultati:
        risposta += f"- {store}: {prezzo} € [Link]({url})\n"

    await update.message.reply_markdown(risposta)

# Avvio del bot
if __name__ == "__main__":
    TOKEN = "TOKEN_TELEGRAM"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("prezzi", prezzi))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("commands", commands))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("store", store_command))

    print("Bot in esecuzione...")
    app.run_polling()
