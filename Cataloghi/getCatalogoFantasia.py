from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

def get_last_page(driver, url):
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Trova tutte le voci nella paginazione
    pagination = soup.select("ul.page-list li a")
    numeri = [int(a.get_text(strip=True)) for a in pagination if a.get_text(strip=True).isdigit()]
    return max(numeri) if numeri else 1

def estrai_giochi_fantasiastore():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=options)
    tutti_giochi = []

    base_url = "https://fantasiastore.it/it/3-giochi-in-scatola"
    last_page = get_last_page(driver, base_url)
    print(f"Trovate {last_page} pagine nel catalogo.")

    for pagina in range(1, last_page + 1):
        url = f"{base_url}?page={pagina}"
        print(f"Scarico pagina {pagina}...")
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        giochi = soup.select("article.product-miniature h3.product-title a")

        if not giochi:
            print(f"Nessun gioco trovato nella pagina {pagina}, interrompo.")
            break

        for g in giochi:
            nome = g.get_text(strip=True)
            link = g["href"]
            tutti_giochi.append({"nome": nome, "link": link})

    driver.quit()
    return tutti_giochi

# Esegui scraping e salva JSON
giochi = estrai_giochi_fantasiastore()

with open("fantasiastore_catalogo.json", "w", encoding="utf-8") as f:
    json.dump(giochi, f, indent=2, ensure_ascii=False)

print(f"\nTrovati e salvati {len(giochi)} giochi.")
