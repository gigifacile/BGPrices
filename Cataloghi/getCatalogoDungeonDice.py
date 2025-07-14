from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

def get_last_page(driver, url):
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Trova tutti i link della paginazione
    pagination = soup.select("li.page-list-item a")
    numeri = [int(a.get_text(strip=True)) for a in pagination if a.get_text(strip=True).isdigit()]
    return max(numeri) if numeri else 1

def estrai_giochi_dungeondice():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=options)
    tutti_giochi = []

    base_url = "https://www.dungeondice.it/253-giochi-da-tavolo?categoria-principale=giochi-da-tavolo&lingua=italiano&condizione=nuovo"
    last_page = get_last_page(driver, base_url)
    print(f"Trovate {last_page} pagine nel catalogo.")

    for pagina in range(1, last_page + 1):
        url = f"{base_url}?page={pagina}" if pagina > 1 else base_url
        print(f"Scarico pagina {pagina}...")
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        giochi = soup.select("div.e-list-product-in")

        if not giochi:
            print(f"Nessun gioco trovato nella pagina {pagina}, interrompo.")
            break

        for gioco in giochi:
            titolo_tag = gioco.select_one("h3.e-list-product-title")
            link_tag = gioco.select_one("a.thumbnail.product-thumbnail")

            if titolo_tag and link_tag:
                nome = titolo_tag.get_text(strip=True)
                link = link_tag["href"]
                tutti_giochi.append({"nome": nome, "link": link})

    driver.quit()
    return tutti_giochi

# Esegui scraping e salva JSON
giochi = estrai_giochi_dungeondice()

with open("dungeondice_catalogo.json", "w", encoding="utf-8") as f:
    json.dump(giochi, f, indent=2, ensure_ascii=False)

print(f"\nTrovati e salvati {len(giochi)} giochi.")
