from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from main import get_prezzo_gioco
import pytz

TOKEN = "7431941125:AAH7woPQaIlfOT_sUBJVhehcOSletH_ZsIY"
rome = pytz.timezone("Europe/Rome")
now = datetime.now(rome)

async def prezzo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        nome_gioco = " ".join(context.args)
        messaggio = get_prezzo_gioco(nome_gioco)
    else:
        messaggio = "❗ Usa il comando così: /prezzo NomeGioco"
    
    await update.message.reply_text(messaggio, parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token("TOKEN").local_timezone(pytz.timezone("Europe/Rome")).build()
    app.add_handler(CommandHandler("prezzo", prezzo_handler))
    app.run_polling()
