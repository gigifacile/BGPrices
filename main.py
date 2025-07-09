
import json
from concurrent.futures import ThreadPoolExecutor
from config import LISTA_PATH
from utils import process_url

# Import scraper functions
from scraper import (
    dungeondice, fantasia, magicmerchant, getyourfun, player1,
    feltrinelli, uplay, dadiemattoncini, covodelnerd
)

def main():
    with open(LISTA_PATH, "r", encoding="utf-8") as f:
        games = json.load(f)

    updated = False
    tasks = []

    scraper_map = {
        "dungeondice.it":     (dungeondice.get_price, "DungeonDice"),
        "fantasiastore.it":   (fantasia.get_price, "FantasiaStore"),
        "magicmerchant.it":   (magicmerchant.get_price, "MagicMerchant"),
        "getyourfun.it":      (getyourfun.get_price, "GetYourFun"),
        "player1.it":         (player1.get_price, "Player1"),
        "lafeltrinelli.it":   (feltrinelli.get_price, "LaFeltrinelli"),
        "uplay.it":           (uplay.get_price, "UPlay"),
        "dadiemattoncini.it": (dadiemattoncini.get_price, "DadiEMattoncini"),
        "ilcovodelnerd.com":  (covodelnerd.get_price, "IlCovoDelNerd")
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
