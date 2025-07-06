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
    except:
        pass
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
    except:
        pass
    return None

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
    except:
        pass

def main():
    try:
        with open(LISTA_PATH, "r", encoding="utf-8") as f:
            games = json.load(f)
    except:
        return

    updated = False

    for game in games:
        name, threshold = game["name"], game["threshold"]
        for url in game["links"]:
            price = None
            fonte = ""
            if "dungeondice.it" in url:
                price = get_price_dungeondice(url)
                fonte = "DungeonDice"
            elif "magicmerchant.it" in url:
                price = get_price_magicmerchant(url)
                fonte = "MagicMerchant"
            if price is not None and price < threshold:
                send_alert(name, price, url)
                game["threshold"] = price
                append_to_storico(name, fonte, price)
                updated = True

    if updated:
        try:
            with open(LISTA_PATH, "w", encoding="utf-8") as f:
                json.dump(games, f, ensure_ascii=False, indent=2)
        except:
            pass

if __name__ == "__main__":
    main()
