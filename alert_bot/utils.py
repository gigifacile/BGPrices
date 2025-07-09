
from telegram_utils import send_alert
from storico import append_to_storico

def clean_surrogates(text):
    return text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")

def process_url(game, url, scraper_func, fonte):
    try:
        price = scraper_func(url)
        if price is not None:
            print(f"{game['name']} - {fonte}: {price:.2f} € (soglia {game['threshold']:.2f} €)".encode("utf-8", "replace").decode("utf-8"))
            if price < game["threshold"]:
                print("→ Nuovo minimo storico! Invio notifica e aggiorno soglia.")
                send_alert(game["name"], price, url)
                game["threshold"] = price
                append_to_storico(game["name"], fonte, price)
                return True
        else:
            print(f"{game['name']} - {fonte}: non disponibile")
    except Exception as e:
        print(f"[Errore {fonte}] {url} → {e}")
    return False
