from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from openai import OpenAI
import time
import re
import json
import sys

# ==== OpenAI API keyini gir ====
client = OpenAI(api_key="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")

# Komut satırı argümanlarını al
if len(sys.argv) < 4:
    print("Kullanım: python crawler.py <search_query> <links_count> <existing_urls_path>")
    sys.exit(1)

search_query = sys.argv[1]
links_count = int(sys.argv[2])
existing_urls_path = sys.argv[3]

# Mevcut url'leri oku
with open(existing_urls_path, 'r', encoding='utf-8') as f:
    existing_urls = set(json.load(f))

# ==== Chrome başlat ====
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 20)

# ==== Google'da arama yap ====
driver.get("https://www.google.com")
time.sleep(2)

search_box = driver.find_element(By.NAME, "q")
search_box.send_keys(search_query)
search_box.send_keys(Keys.RETURN)

time.sleep(25)

# ==== Linkleri çekmek için döngü (links_count kadar yeni link toplanana kadar) ====
links = []
page = 1
while len(links) < links_count:
    print(f"\n🔎 Google {page}. sayfa taranıyor...")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div#search a")))
    search_results = driver.find_elements(By.CSS_SELECTOR, "div#search a")

    for result in search_results:
        href = result.get_attribute("href")
        if href and href.startswith("http") and "google" not in href:
            if href not in links and href not in existing_urls:
                links.append(href)
        if len(links) >= links_count:
            break

    # Sonraki sayfaya geç
    if len(links) < links_count:
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.ID, "pnnext")))
            next_button.click()
            page += 1
            time.sleep(2)
        except:
            print("🔚 Daha fazla sayfa bulunamadı.")
            break

print(f"\n🔗 Toplam {len(links)} yeni link bulundu.")

results = []
failed_results = []

# ==== Her siteye girip bilgi topla ====
for index, link in enumerate(links, start=1):
    print(f"\n[{index}] Siteye gidiliyor: {link}")
    try:
        driver.get(link)
        # Sayfa tamamen görünür hale gelene kadar bekle
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        html = driver.page_source

        # Gelişmiş regex ile mail ve tel çek (hem mailto: hem düz mail)
        mailto_emails = re.findall(r"mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", html)
        phones = re.findall(r"(?:(?:\+|00)[1-9][0-9\s\-\(\)]{6,})", html)
        email = mailto_emails[0] if mailto_emails else ""
        phone = phones[0] if phones else ""

        if not mailto_emails:
            print(f"❌ mailto: bulunamadı, sadece website failed_output.json'a eklenecek.")
            failed_results.append({
                "website": link,
                "email": "",
                "phone": ""
            })
            continue

        results.append({
            "website": link,
            "email": email,
            "phone": phone
        })
        print(f"✅ Çekildi: Email: {email}, Telefon: {phone}")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        continue

# ==== Sonuçları JSON olarak kaydet ====
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

with open("failed_output.json", "w", encoding="utf-8") as f:
    json.dump(failed_results, f, ensure_ascii=False, indent=2)

print("\n✅ Tüm işlemler tamamlandı. Sonuçlar output.json ve failed_output.json dosyasına yazıldı.")

# Tarayıcıyı kapat
driver.quit()
