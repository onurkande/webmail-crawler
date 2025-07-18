from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from openai import OpenAI
import json
import time
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# OpenAI istemcisi
client = OpenAI(api_key="")  # kendi key'ini buraya yaz

# Selenium başlat
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# 1. Google'da arama yap
driver.get("https://www.google.com")
time.sleep(2)

# Doğrudan siteye git
first_link = "https://innoapps-agentur.de/en/software-consulting/"
print("Hedef site:", first_link)

search_box = driver.find_element(By.NAME, "q")
search_box.send_keys(first_link)
search_box.send_keys(Keys.RETURN)
time.sleep(25)

# WebDriverWait ile sayfanın tam yüklenmesini bekle
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
except Exception as e:
    print("Sayfa yüklenirken hata:", e)

driver.get(first_link)
# Yine sayfanın yüklenmesini bekle
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
except Exception as e:
    print("Sayfa yüklenirken hata:", e)

time.sleep(2)

# 3. Sayfa HTML'ini al ve kaydet
html_content = driver.page_source
print("Ana sayfa HTML uzunluğu:", len(html_content))

# Regex ile mailto: ve tel: çek
import re
mailto_matches = re.findall(r"mailto:([a-zA-Z0-9_.+%-]+@[a-zA-Z0-9.-]+)", html_content)
tel_matches = re.findall(r"tel:([\d\+\-\s]+)", html_content)

email = mailto_matches[0] if mailto_matches else ""
phone = tel_matches[0] if tel_matches else ""
website = first_link

# Eğer mailto: veya tel: bulunamazsa, LLM'ye son 10000 karakteri gönder
llm_needed = (not email or not phone)

if llm_needed:
    print("Regex ile e-posta veya telefon bulunamadı, LLM'ye sorulacak.")
    html_for_llm = html_content[-10000:]
else:
    html_for_llm = None

# HTML'i dosyaya yaz
with open("page_source.txt", "w", encoding="utf-8") as f:
    f.write(html_content)

# 4. Eğer contact linki varsa oraya git
def go_to_contact_page():
    possible_keywords = ["contact", "kontakt", "impressum"]
    links = driver.find_elements(By.TAG_NAME, "a")

    for link in links:
        href = link.get_attribute("href")
        text = link.text.lower()
        if any(keyword in text or (href and keyword in href.lower()) for keyword in possible_keywords):
            print(f"🔎 Contact sayfası bulundu: {href}")
            driver.get(href)
            time.sleep(3)
            return True
    print("❌ Contact sayfası bulunamadı.")
    return False

# Eğer sayfada e-posta veya telefon yoksa contact sayfasına git
if "@" not in html_content and "tel:" not in html_content:
    go_to_contact_page()
    html_content = driver.page_source  # yeni sayfa içeriğini al
    with open("contact_page_source.txt", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("📄 Contact sayfasının HTML'i kaydedildi.")

# Tarayıcıyı kapat
driver.quit()

# 5. GPT'ye gönder
if llm_needed:
    prompt = f"""
Aşağıda bir web sitesinin HTML içeriğinden çekilmiş e-posta adresleri ve telefon numaraları var.

E-posta adresleri:
{mailto_matches}

Telefon numaraları:
{tel_matches}

Website: {first_link}

Lütfen bu e-posta adreslerinden bu web sitesine en uygun olanı (en mantıklı olanı) seç. 
Kriter: Alan adıyla uyumlu, bozulmamış, gerçek bir e-posta gibi görüneni seç.

Aşağıdaki formatta sadece EN UYGUN olan e-posta ve telefon numarasını JSON olarak döndür:

{{
  "email": "seçilen@email.com",
  "phone": "seçilen_telefon",
  "website": "{first_link}"
}}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # 6. Yanıtı kaydet
    result_text = response.choices[0].message.content
    print("🤖 AI çıktısı:\n", result_text)

    with open("deneme.json", "w", encoding="utf-8") as f:
        f.write(result_text)
    print("✅ Çıktı deneme.json dosyasına kaydedildi.")
else:
    # Regex ile bulduysan direkt kaydet
    result = {
        "email": email,
        "phone": phone,
        "website": website
    }
    print("Regex ile bulunan sonuç:", result)
    with open("deneme.json", "w", encoding="utf-8") as f:
        import json
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("✅ Çıktı deneme.json dosyasına kaydedildi.")