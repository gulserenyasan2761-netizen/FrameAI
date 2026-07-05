import time
import os
import sys
import json
import warnings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from groq import Groq

# Terminaldeki gereksiz log ve uyarıları gizle
warnings.filterwarnings("ignore", category=UserWarning)

# =====================================================================
# AYARLAR
# =====================================================================
GROQ_API_KEY = "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"
YAYIN_URL = "https://www.youtube.com/watch?v=5jka-H-Hvy4"

# Groq Yapay Zeka İstemcisi
groq_client = Groq(api_key=GROQ_API_KEY)

# =====================================================================
# CHROME TARAYICI AYAĞA KALDIRMA
# =====================================================================
chrome_options = Options()
chrome_options.add_argument("--headless") # Bulut için şart
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

print("🌐 Chrome tarayıcı başlatılıyor...")
driver = webdriver.Chrome(options=chrome_options)

# ÇEREZLERİ YÜKLE
print(f"🔗 Canlı yayın sayfasına gidiliyor: {YAYIN_URL}")
driver.get(YAYIN_URL)
time.sleep(5)

try:
    with open('cookies.txt', 'r') as f:
        cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(5)
    print("✅ Çerezler başarıyla yüklendi!")
except Exception as e:
    print(f"⚠️ Çerezler yüklenemedi, giriş yapmamış olabilirsiniz: {e}")

# =====================================================================
# CHAT PENCERESİNE SIZMA
# =====================================================================
try:
    chat_iframe = driver.find_element(By.CSS_SELECTOR, "#chatframe")
    driver.switch_to.frame(chat_iframe)
    print("✅ Canlı chat odasına başarıyla odaklanıldı!")
except Exception as e:
    print(f"⚠️ Sohbet penceresi bulunamadı: {e}")

okunan_mesajlar = set()

# İlk mesaj
try:
    chat_kutusu = driver.find_element(By.CSS_SELECTOR, "#input.yt-live-chat-text-input-field-renderer")
    chat_kutusu.click()
    chat_kutusu.send_keys("Merhaba ben FRAMEAI. Sorularınızı !bot yazarak sorabilirsiniz.")
    chat_kutusu.send_keys(Keys.ENTER)
except:
    pass

# =====================================================================
# ANA DÖNGÜ
# =====================================================================
while True:
    try:
        mesaj_elementleri = driver.find_elements(By.CSS_SELECTOR, "yt-live-chat-text-message-renderer")
        for el in mesaj_elementleri:
            msg_id = el.get_attribute("id")
            if msg_id in okunan_mesajlar: continue
            
            kullanici = el.find_element(By.CSS_SELECTOR, "#author-name").text
            mesaj_metni = el.find_element(By.CSS_SELECTOR, "#message").text
            okunan_mesajlar.add(msg_id)
            
            if mesaj_metni.startswith("!bot"):
                soru = mesaj_metni.replace("!bot", "").strip()
                if soru:
                    chat_completion = groq_client.chat.completions.create(
                        messages=[{"role": "system", "content": "Kısa ve düzgün Türkçe cevap ver. Maks 80 karakter, markdown yok."},
                                  {"role": "user", "content": soru}],
                        model="llama-3.1-8b-instant",
                        max_tokens=40
                    )
                    bot_cevap = chat_completion.choices[0].message.content.replace("*", "").replace("#", "")
                    tam_cevap = f"@{kullanici} {bot_cevap}"[:195]
                    
                    chat_kutusu = driver.find_element(By.CSS_SELECTOR, "#input.yt-live-chat-text-input-field-renderer")
                    chat_kutusu.click()
                    chat_kutusu.send_keys(tam_cevap)
                    chat_kutusu.send_keys(Keys.ENTER)
                    print(f"🤖 Bot Cevap Verdi: {tam_cevap}")
                    time.sleep(4)
        
        if len(okunan_mesajlar) > 300: okunan_mesajlar.clear()
        time.sleep(2)
    except Exception as e:
        time.sleep(4)