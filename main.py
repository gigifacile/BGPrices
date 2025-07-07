import requests, re, json, csv, datetime

TOKEN = "7431941125:AAH7woPQaIlfOT_sUBJVhehcOSletH_ZsIY"
CHAT_ID = "102733635"
LISTA_PATH = "Lista.json"
STORICO_PATH = "storico_prezzi.csv"

def send_alert(name, price, url):
    message = f"🎲 *{name}* nuovo minimo storico: {price:.2f}€!\n🔗 {url}"
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
    )

def get_price_fantasia(url):
    if not url:
        return "Non venduto"

    try:
        response = requests.get(url, timeout=10)
        html = response.text

        # Controllo disponibilità
        disponibile = re.search(
            r'<i[^>]*class=["\']fa fa-circle-o-notch[^>]*>.*?</i>\s*(.*?)\s*</button>',
            html
        )
        if disponibile and "Aggiungi al carrello" not in disponibile.group(1):
            return None

        # Estrazione prezzo
        prezzo = re.search(
            r'<span itemprop="price" class="product-price" content="(\d+\.\d+)">',
            html
        )
        if not prezzo:
            return None

        prezzo_pulito = prezzo.group(1).replace(",", ".")
        prezzo_numerico = float(prezzo_pulito)
        return prezzo_numerico

    except Exception as e:
        print(f"[Errore FantasiaStore] {url} → {e}")
        return None

def get_price_dungeondice(url):
    if not url: return None
    try:
        html = requests.get(url, timeout=10).text
        if re.search(r'<span[^>]*>remove_shopping_cart<\/span>\s*<span>(.*?)<\/span>', html): return None
        if re.search(r'<span[^>]*>Preordina<\/span>', html, re.I): return None

        m = re.search(r'<div[^>]*class=["\']display-price["\'][^>]*>Prezzo(?: Speciale)?:\s*(\d+,\d+)', html)
        if m: return float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[Errore DungeonDice] {url} → {e}")
    return None

def get_price_magicmerchant(url):
    if not url: return None
    try:
        html = requests.get(url, timeout=10).text
        if re.search(r'<p class="outofstock availability verbose availability-message">', html): return None
        m = re.search(r'<p class="price_color">(\d{1,3},\d{2})', html)
        if m: return float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[Errore MagicMerchant] {url} → {e}")
    return None

def get_price_getyourfun(url):
    if not url: return None
    try:
        html = requests.get(url, timeout=10).text

        # Sezione: Non disponibile
        if re.search(r'<div class="mar_b6">(.*?)<\/div>', html):
            return None

        # Sezione: Ristampa
        if re.search(r'<div class="st_sticker_block">\s*<div class="st_sticker layer_btn\s+st_sticker_static\s+st_sticker_14\s*">\s*<span class="st_sticker_text"[^>]*>(.*?)<\/span>', html, re.I):
            return None

        # Sezione: Prezzo
        m = re.search(r'<span class="price"[^>]*content="([\d.,]+)"', html)
        if m:
            prezzo = m.group(1).replace(",", ".")
            return float(prezzo)
    except Exception as e:
        pass
    return None

def get_price_player1(url):
    if not url:
        return "Non venduto"
    
    try:
        response = requests.get(url, timeout=10)
        html = response.text

        # Controllo disponibilità
        disponibile = re.search(r'<p class="stock out-of-stock wd-style-default">(.*?)<\/p>', html)
        print("Disponibilità:", disponibile)
        if disponibile:
            return None

        # Parsing prezzo attuale scontato
        prezzo = re.search(r'<p class="price">.*?<ins[^>]*>.*?<bdi>(\d{1,3},\d{2})', html, re.DOTALL)
        print("Match prezzo:", prezzo)
        if not prezzo:
            return None

        prezzo_pulito = prezzo.group(1).replace(",", ".")
        print("Prezzo pulito:", prezzo_pulito)

        prezzo_numerico = float(prezzo_pulito)
        return prezzo_numerico

    except Exception as e:
        print(f"[Errore Player1] {url} → {e}")
        return "Errore"

import requests
import re

def get_price_feltrinelli(url):
    if not url:
        return "Non venduto"
    
    try:
        response = requests.get(url, timeout=10)
        html = response.text

        # Controllo disponibilità (Avvisami = non disponibile)
        disponibile = re.search(
            r'<button[^>]*class=["\'][^"\']*cc-button--secondary[^"\']*["\'][^>]*>\s*<img[^>]*alt=["\'][^"\']*["\'][^>]*>\s*(.*?)\s*</button>',
            html,
            re.IGNORECASE
        )
        if disponibile and "Avvisami" in disponibile.group(1):
            return None

        # Estrazione prezzo
        prezzo = re.search(
            r'<div class="cc-buy-box-container">[\s\S]*?<span class="cc-price">([\d.,]+)\s*€</span>',
            html
        )
        if not prezzo:
            return None

        prezzo_pulito = prezzo.group(1).replace(",", ".")
        prezzo_numerico = float(prezzo_pulito)
        return prezzo_numerico

    except Exception as e:
        print(f"[Errore Feltrinelli] {url} → {e}")
        return "Errore"

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

def main():
    with open(LISTA_PATH, "r", encoding="utf-8") as f:
        games = json.load(f)

    updated = False

    for game in games:
        name, threshold = game["name"], game["threshold"]
        for url in game["links"]:
            if "dungeondice.it" in url:
                price = get_price_dungeondice(url); 
                fonte = "DungeonDice"
            elif "fantasiastore.it" in url:
                price = get_price_feltrinelli(url); 
                fonte = "LaFeltrinelli"
            elif "magicmerchant.it" in url:
                price = get_price_magicmerchant(url); 
                fonte = "MagicMerchant"
            elif "getyourfun.it" in url:
                price = get_price_getyourfun(url); 
                fonte = "GetYourFun"
            elif "player1.it" in url:
                price = get_price_player1(url); 
                fonte = "Player1"
            elif "lafeltrinelli.it" in url:
                price = get_price_feltrinelli(url); 
                fonte = "LaFeltrinelli"
            else:
                continue

            if price is not None:
                print(f"{name} - {fonte}: {price:.2f} € (soglia {threshold:.2f} €)")
                if price < threshold:
                    print(f"→ Nuovo minimo storico! Invio notifica e aggiorno soglia.")
                    send_alert(name, price, url)
                    game["threshold"] = price
                    append_to_storico(name, fonte, price)
                    updated = True
            else:
                print(f"{name} - {fonte}: non disponibile")

    if updated:
        with open(LISTA_PATH, "w", encoding="utf-8") as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        print("✅ Soglie aggiornate e storico salvato.")

if __name__ == "__main__":
    main()
