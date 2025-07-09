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


def get_price_dungeondice(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(r'<span[^>]*>remove_shopping_cart</span>\s*<span>(.*?)</span>', html) or \
           re.search(r'<span[^>]*>Preordina</span>', html, re.I):
            return None
        m = re.search(
            r'<div[^>]*class=["\']display-price["\'][^>]*>Prezzo(?: Speciale)?:\s*(\d+,\d+)',
            html
        )
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore DungeonDice] {url} → {e}")
        return None


def get_price_magicmerchant(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(
            r'<p class="outofstock availability verbose availability-message">', html
        ):
            return None
        m = re.search(r'<p class="price_color">(\d{1,3},\d{2})', html)
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore MagicMerchant] {url} → {e}")
        return None


def get_price_getyourfun(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(r'<div class="mar_b6">(.*?)</div>', html) or \
           re.search(r'<div class="st_sticker_block">.*?st_sticker_14.*?<span.*?>(.*?)</span>', html, re.I | re.DOTALL):
            return None
        m = re.search(r'<span class="price"[^>]*content="([\d.,]+)"', html)
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore GetYourFun] {url} → {e}")
        return None


def get_price_player1(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(r'<p class="stock out-of-stock wd-style-default">(.*?)</p>', html):
            return None
        prezzo = re.search(
            r'<p class="price">.*?<ins[^>]*>.*?<bdi>(\d{1,3},\d{2})',
            html,
            re.DOTALL
        )
        return float(prezzo.group(1).replace(",", ".")) if prezzo else None
    except Exception as e:
        print(f"[Errore Player1] {url} → {e}")
        return None


def get_price_feltrinelli(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        disponibile = re.search(
            r'<button[^>]*class=["\'][^"\']*cc-button--secondary[^"\']*["\'][^>]*>\s*<img[^>]*alt=["\'][^"\']*["\'][^>]*>\s*(.*?)\s*</button>',
            html,
            re.I
        )
        if disponibile and "Avvisami" in disponibile.group(1):
            return None
        prezzo = re.search(
            r'<div class="cc-buy-box-container">[\s\S]*?<span class="cc-price">([\d.,]+)\s*€</span>',
            html
        )
        return float(prezzo.group(1).replace(",", ".")) if prezzo else None
    except Exception as e:
        print(f"[Errore Feltrinelli] {url} → {e}")
        return None


def get_price_uplay(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(r'<div class="notOrderableText[^>]*">\s*(.*?)\s*</div>', html, re.DOTALL | re.I):
            return None
        availability = re.search(
            r'<span class="shipping-info[^>]*">\s*(.*?)\s*</span>', html, re.DOTALL | re.I
        )
        if not availability or "disponibile" not in availability.group(1).lower():
            return None
        prezzo = re.search(
            r'<div class="promo-price">\s*(\d{1,3},\d{2})', html, re.DOTALL | re.I
        ) or re.search(
            r'<span class="price fw-bold">\s*(\d{1,3},\d{2})', html, re.DOTALL | re.I
        )
        return float(prezzo.group(1).replace(",", ".")) if prezzo else None
    except Exception:
        return None


def get_price_dadiemattoncini(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(r'<span\s+style="margin-left:auto;.*?display:inline-block;">([^<]*)</span>', html, re.I):
            return None
        price = re.search(
            r'<span class="product-price"[^>]*>\s*&euro;\s*(\d+,\d+)\s*</span>', html
        )
        return float(price.group(1).replace(",", ".")) if price else None
    except Exception as e:
        print(f"[Errore DadiEMattoncini] {url} → {e}")
        return None


def get_price_covo_del_nerd(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(r'<p class="stock out-of-stock">\s*(.*?)\s*</p>', html, re.I):
            return None
        if re.search(r'Ordina Ora \(([^)]+)\)</button>', html):
            return None
        matches = re.findall(
            r'<\s*span[^>]*class\s*=\s*"woocommerce-Price-amount amount"[^>]*>\s*<\s*bdi[^>]*>\s*([\d]+,[\d]+)',
            html
        )
        if matches:
            return float(matches[-1].replace(",", "."))
        return None
    except Exception as e:
        print(f"[Errore CovoDelNerd] {url} → {e}")
        return None

def get_price_lsgiochi(url):
    if not url:
        return None
    
    response = requests.get(url, timeout=10)
    html = response.text

    # Verifica se è esaurito
    sold_out_match = re.search(r'<div class="product-sticker product-sticker--sold-out">\s*(.*?)\s*</div>', html)
    if sold_out_match:
        return None

    # Estrai il prezzo
    price_match = re.search(r'product__price__price">([\d.,]+)', html)
    if price_match:
        prezzo_pulito = price_match.group(1).replace(',', '.')
        try:
            return float(prezzo_pulito)
        except ValueError:
            return None

    return None

def get_price_dragonstore(url):
    if not url:
        return None

    try:
        response = requests.get(url, timeout=10)
        html = response.text
    except Exception:
        return None

    # Verifica disponibilità
    disponibilita_match = re.search(
        r'<td[^>]*class=["\']availability["\'][^>]*>\s*<span class=["\']fullAV["\'][^>]*>(.*?)</span>\s*</td>',
        html,
        re.IGNORECASE
    )
    if not disponibilita_match:
        return None

    # Estrai il prezzo
    prezzo_match = re.search(r'<span class="mainPriceAmount">([\d,]+)</span>', html)
    if not prezzo_match:
        return None

    try:
        prezzo_pulito = prezzo_match.group(1).replace(',', '.')
        return float(prezzo_pulito)
    except ValueError:
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
        "dungeondice.it":     (get_price_dungeondice, "DungeonDice"),
        "fantasiastore.it":   (get_price_fantasia, "FantasiaStore"),
        "magicmerchant.it":   (get_price_magicmerchant, "MagicMerchant"),
        "getyourfun.it":      (get_price_getyourfun, "GetYourFun"),
        "player1.it":         (get_price_player1, "Player1"),
        "lafeltrinelli.it":   (get_price_feltrinelli, "LaFeltrinelli"),
        "uplay.it":           (get_price_uplay, "UPlay"),
        "dadiemattoncini.it": (get_price_dadiemattoncini, "DadiEMattoncini"),
        "ilcovodelnerd.com":  (get_price_covo_del_nerd, "IlCovoDelNerd"),
        "lsgiochi.it":        (get_price_lsgiochi, "LSGiochi"),
        "dragonstore.it":     (get_price_dragonstore, "DragonStore"),
    }

    with ThreadPoolExecutor(max_workers=10) as executor:
        for game in games:
            for url in game["links"]:
                for domain, (scraper_func, fonte) in scraper_map.items():
                    if domain in url:
                        tasks.append(executor.submit(process_url, game, url, scraper_func, fonte))
                        break

    for task in tasks:
        if task.result():
            updated = True

    if updated:
        with open(LISTA_PATH, "w", encoding="utf-8") as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        print("✅ Soglie aggiornate e storico salvato.")


if __name__ == "__main__":
    main()
