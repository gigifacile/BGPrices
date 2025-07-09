import sys
import io
import re
import csv
import json
import datetime
import requests
import os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# Forza l'output in UTF-8 con gestione errori
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "7431941125:AAH7woPQaIlfOT_sUBJVhehcOSletH_ZsIY"
CHAT_ID = "102733635"
LISTA_PATH = "Lista.json"
STORICO_PATH = "storico_prezzi.csv"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}


def clean_surrogates(text):
    return text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")


def send_alert(name, price, url):
    message = f"🎲 *{name}* nuovo minimo storico: {price:.2f}€!\n🔗 {url}"
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
    except Exception as e:
        print(f"[Errore Telegram] {e}")


def append_to_storico(name, fonte, price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = ["data", "gioco", "sito", "prezzo"]
    row = [now, name, fonte, f"{price:.2f}"]
    try:
        with open(STORICO_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(header)
            writer.writerow(row)
    except Exception as e:
        print(f"[Errore storico] {e}")


def get_price_fantasia(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=20).text
        disponibile = re.search(
            r'<i[^>]*class=["\']fa fa-circle-o-notch[^>]*>.*?</i>\s*(.*?)\s*</button>',
            html,
        )
        if disponibile and "Aggiungi al carrello" not in disponibile.group(1):
            return None
        prezzo = re.search(
            r'<span itemprop="price" class="product-price" content="(\d+\.\d+)">', html
        )
        return float(prezzo.group(1).replace(",", ".")) if prezzo else None
    except Exception as e:
        print(f"[Errore FantasiaStore] {url} → {e}")
        return None

def process_url(game, url, scraper_func, fonte):
    try:
        price = scraper_func(url)
        if price is not None:
            print(
                f"{game['name']} - {fonte}: {price:.2f} € (soglia {game['threshold']:.2f} €)"
                .encode("utf-8", "replace").decode("utf-8")
            )
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


def main():
    with open(LISTA_PATH, "r", encoding="utf-8") as f:
        games = json.load(f)

    updated = False
    tasks = []

    scraper_map = {
        "fantasiastore.it":   (get_price_fantasia, "FantasiaStore"),
    }

    # Dizionario per salvare i prezzi attuali
    prezzi_attuali = []

    # Eseguo i controlli e raccolgo prezzi per notifiche e storico
    with ThreadPoolExecutor(max_workers=10) as executor:
        for game in games:
            # Per ogni gioco creo un dizionario dei prezzi per ogni store
            prezzi_per_gioco = {"name": game["name"], "prezzi": {}}
            for url in game["links"]:
                for domain, (scraper_func, fonte) in scraper_map.items():
                    if domain in url:
                        price = scraper_func(url)
                        if price is not None:
                            prezzi_per_gioco["prezzi"][fonte] = price
                        break
            prezzi_attuali.append(prezzi_per_gioco)

    # Ora eseguo di nuovo i controlli con notifiche (puoi tenerli se vuoi)
    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = []
        for game in games:
            for url in game["links"]:
                for domain, (scraper_func, fonte) in scraper_map.items():
                    if domain in url:
                        tasks.append(executor.submit(process_url, game, url, scraper_func, fonte))
                        break

        for task in tasks:
            if task.result():
                updated = True

    # Salvataggio prezzi attuali in JSON, sempre sovrascrivendo
    with open("PrezziAttuali.json", "w", encoding="utf-8") as f:
        json.dump(prezzi_attuali, f, ensure_ascii=False, indent=2)

    # Se aggiornato, riscrivo lista e storico
    if updated:
        with open(LISTA_PATH, "w", encoding="utf-8") as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        print("✅ Soglie aggiornate e storico salvato.")


if __name__ == "__main__":
    main()
