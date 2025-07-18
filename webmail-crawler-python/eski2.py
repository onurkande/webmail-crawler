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

# ==== OpenAI API keyini gir ====
client = OpenAI(api_key="")

# ==== Chrome başlat ====
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 20)

# ==== Google'da arama yap ====
driver.get("https://www.google.com")
time.sleep(2)

search_query = "software agentur site:de"
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys(search_query)
search_box.send_keys(Keys.RETURN)

time.sleep(25)

# ==== Linkleri çekmek için döngü (300 link toplanana kadar) ====
links = []
page = 1
while len(links) < 300:
    print(f"\n🔎 Google {page}. sayfa taranıyor...")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div#search a")))
    search_results = driver.find_elements(By.CSS_SELECTOR, "div#search a")

    for result in search_results:
        href = result.get_attribute("href")
        if href and href.startswith("http") and "google" not in href:
            if href not in links:
                links.append(href)
        if len(links) >= 300:
            break

    # Sonraki sayfaya geç
    if len(links) < 300:
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.ID, "pnnext")))
            next_button.click()
            page += 1
            time.sleep(2)
        except:
            print("🔚 Daha fazla sayfa bulunamadı.")
            break

print(f"\n🔗 Toplam {len(links)} link bulundu.")

results = []

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
        emails = re.findall(r"(?:mailto:)?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", html)
        phones = re.findall(r"(?:(?:\+|00)[1-9][0-9\s\-\(\)]{6,})", html)
        email = emails[0] if emails else ""
        phone = phones[0] if phones else ""

        # Eğer mailto: içeren e-posta bulunamazsa 15 saniye bekle ve tekrar kontrol et
        if not any('mailto:' in m for m in re.findall(r'(mailto:[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', html)):
            print("✋ mailto: bulunamadı, 15 saniye daha bekleniyor...")
            time.sleep(15)
            html = driver.page_source
            emails = re.findall(r"(?:mailto:)?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", html)
            email = emails[0] if emails else ""
            # mailto: tekrar kontrol
            if not any('mailto:' in m for m in re.findall(r'(mailto:[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', html)):
                print(f"❌ mailto: hala bulunamadı, sayfa atlanıyor ve HTML kaydediliyor (failed_{index}.txt)")
                with open(f"failed_{index}.txt", "w", encoding="utf-8") as failf:
                    failf.write(html)
                continue

        llm_needed = (not email or not phone)

        # Eğer eksikse yapay zekaya sor
        if llm_needed:
            print("🧠 Regex yetersiz, GPT kullanılıyor...")
            html_for_llm = html[-10000:]
            prompt = f"""
Aşağıda bir web sayfasının HTML içeriği var. Bu içerikten varsa e-posta ve telefon bilgilerini çıkar:

{html_for_llm}

Sonucu aşağıdaki JSON formatında ver:
{{
  "email": "...",
  "phone": "...",
  "website": "{link}"
}}
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            try:
                llm_output = json.loads(response.choices[0].message.content)
                email = llm_output.get("email", "")
                phone = llm_output.get("phone", "")
            except Exception as e:
                print("⚠️ JSON parse hatası:", e)

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

print("\n✅ Tüm işlemler tamamlandı. Sonuçlar output.json dosyasına yazıldı.")

# Tarayıcıyı kapat
driver.quit()
