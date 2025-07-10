import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# La tua funzione
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

# Informazioni relative al bot
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Questo bot controlla i prezzi dei giochi da tavolo ogni ora e notifica l'utente se un gioco raggiunge il suo minimo storico.")

# Funzione handler per il comando /prezzi
async def prezzi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Scrivi il nome del gioco dopo /prezzi, es: /prezzi Scythe")
        return
    
    nome_gioco = " ".join(context.args)
    risultati = get_prezzi_gioco(nome_gioco)

    if not risultati:
        await update.message.reply_text(f"Gioco '{nome_gioco}' non trovato.")
        return

    # Formatto i risultati in una risposta testuale
    risposta = f"Prezzi per *{nome_gioco}*:\n"
    for store, prezzo, url in risultati:
        risposta += f"- {store}: {prezzo} € [Link]({url})\n"

    await update.message.reply_markdown(risposta)

# Avvio del bot
if __name__ == "__main__":
    TOKEN = "7431941125:AAH7woPQaIlfOT_sUBJVhehcOSletH_ZsIY"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("prezzi", prezzi))
    app.add_handler(CommandHandler("info", info))

    print("Bot in esecuzione...")
    app.run_polling()
