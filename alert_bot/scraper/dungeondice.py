
import re
import requests
from config import DEFAULT_HEADERS

def get_price(url):
    if not url:
        return None
    try:
        html = requests.get(url, headers=DEFAULT_HEADERS, timeout=10).text
        if re.search(r'<span[^>]*>remove_shopping_cart</span>\s*<span>(.*?)</span>', html) or            re.search(r'<span[^>]*>Preordina</span>', html, re.I):
            return None
        m = re.search(r'<div[^>]*class=["\']display-price["\'][^>]*>Prezzo(?: Speciale)?:\s*(\d+,\d+)', html)
        return float(m.group(1).replace(",", ".")) if m else None
    except Exception as e:
        print(f"[Errore DungeonDice] {url} → {e}")
        return None
