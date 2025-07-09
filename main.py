import sys
import io
import re
import csv
import json
import datetime
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os

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
        if re.search(r'Prodotto esaurito', html, re.I):
            return None
        price = re.search(
            r'<span class="price"[^>]*>\s*(\d+,\d+)\s*€\s*</span>', html
        )
        return float(price.group(1).replace(",", ".")) if price else None
    except Exception as e:
        print(f"[Errore CovoDelNerd] {url} → {e}")
        return None


PRICE_GETTERS = {
    "FantasiaStore": get_price_fantasia,
    "DungeonDice": get_price_dungeondice,
    "MagicMerchant": get_price_magicmerchant,
    "GetYourFun": get_price_getyourfun,
    "Player1": get_price_player1,
    "Feltrinelli": get_price_feltrinelli,
    "Uplay": get_price_uplay,
    "DadiEMattoncini": get_price_dadiemattoncini,
    "CovoDelNerd": get_price_covo_del_nerd,
}


def main():
    # Creo PrezziAttuali.json se non esiste
    if not os.path.exists("PrezziAttuali.json"):
        with open("PrezziAttuali.json", "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    # Carica lista giochi
    try:
        with open(LISTA_PATH, "r", encoding="utf-8") as f:
            lista = json.load(f)
    except Exception as e:
        print(f"[Errore Lista.json] {e}")
        return

    prezzi_attuali = {}

    def process_gioco(gioco):
        nome = gioco.get("nome")
        prezzi_attuali[nome] = {}
        for store, url in gioco.get("links", {}).items():
            getter = PRICE_GETTERS.get(store)
            if getter:
                prezzo = getter(url)
                if prezzo is not None:
                    prezzi_attuali[nome][store] = prezzo

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_gioco, lista)

    # Salvo prezzi attuali su file (questa parte è da aggiungere in futuro)

    # Qui puoi continuare con la logica di confronto e invio notifiche

if __name__ == "__main__":
    main()
